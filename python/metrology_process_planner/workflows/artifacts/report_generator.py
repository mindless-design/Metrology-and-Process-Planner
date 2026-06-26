"""Report artifact generator handlers."""

from __future__ import annotations

from dataclasses import replace
from pathlib import Path

from metrology_process_planner.domains.session import (
    ArtifactRecord,
    ModeRegistry,
    ReportRecord,
    SessionRecord,
)
from metrology_process_planner.persistence.paths import SessionPaths
from metrology_process_planner.reporting import ReportGenerationService, ReportRequest
from metrology_process_planner.workflows.artifacts.generators import ArtifactGenerationResult
from metrology_process_planner.workflows.editor.builder import SessionDocumentBuilder

_FORMAT_BY_TYPE = {
    "powerpoint_deck": "pptx",
    "pdf_report": "pdf",
    "csv_export": "csv",
    "image_bundle": "images.zip",
}


def regenerate_report_artifact(
    session: SessionRecord,
    artifact: ArtifactRecord,
    paths: SessionPaths,
    mode_registry: ModeRegistry | None = None,
) -> ArtifactGenerationResult:
    """Regenerate a saved report output from canonical session data."""

    report = _report_for_artifact(session, artifact)
    if report is None:
        raise RuntimeError(f"No report record owns artifact {artifact.id}.")
    clean_session = _without_report_outputs(session, report.id)
    request = ReportRequest(
        clean_session.id,
        report.report_type,
        output_formats=_output_formats(session, report, artifact),
        output_dir=_output_dir(paths, artifact),
    )
    result = ReportGenerationService(mode_registry=mode_registry).generate(
        SessionDocumentBuilder(mode_registry=mode_registry).build(clean_session),
        request,
        paths.folder,
    )
    if result.updated_session is None:
        raise RuntimeError(result.message or "Report regeneration did not complete.")
    generated = _generated_artifact(result.updated_session, artifact)
    if generated is None:
        raise RuntimeError(f"Generator did not produce report artifact {artifact.id}.")
    return ArtifactGenerationResult(generated, result.updated_session)


def _report_for_artifact(
    session: SessionRecord,
    artifact: ArtifactRecord,
) -> ReportRecord | None:
    return next(
        (
            report
            for report in session.reports
            if report.id == artifact.owner.owner_id
            or artifact.id in set((report.artifact_refs or {}).values())
        ),
        None,
    )


def _without_report_outputs(session: SessionRecord, report_id: str) -> SessionRecord:
    artifacts = {
        artifact_id: artifact
        for artifact_id, artifact in (session.artifacts or {}).items()
        if not _owned_by_report(artifact, report_id)
    }
    reports = tuple(report for report in session.reports if report.id != report_id)
    return replace(session, artifacts=artifacts, reports=reports)


def _output_formats(
    session: SessionRecord,
    report: ReportRecord,
    artifact: ArtifactRecord,
) -> tuple[str, ...]:
    if artifact.type in _FORMAT_BY_TYPE:
        return (_FORMAT_BY_TYPE[artifact.type],)
    formats = tuple(_report_artifact_formats(session, report))
    return formats or ("pptx",)


def _output_dir(paths: SessionPaths, artifact: ArtifactRecord) -> Path | None:
    if not artifact.relative_path:
        return None
    parent = Path(artifact.relative_path).parent
    if str(parent) in {"", "."}:
        return None
    return paths.folder / parent


def _generated_artifact(
    session: SessionRecord,
    source: ArtifactRecord,
) -> ArtifactRecord | None:
    artifacts = session.artifacts or {}
    if source.id in artifacts:
        return artifacts[source.id]
    return next(
        (
            artifact
            for artifact in artifacts.values()
            if _matches_generated_source(artifact, source)
        ),
        None,
    )


def _owned_by_report(artifact: ArtifactRecord, report_id: str) -> bool:
    return artifact.owner.owner_type == "report" and artifact.owner.owner_id == report_id


def _report_artifact_formats(
    session: SessionRecord,
    report: ReportRecord,
) -> tuple[str, ...]:
    artifacts = session.artifacts or {}
    return tuple(
        _FORMAT_BY_TYPE[item.type]
        for artifact_id in (report.artifact_refs or {}).values()
        if (item := artifacts.get(artifact_id)) is not None and item.type in _FORMAT_BY_TYPE
    )


def _matches_generated_source(artifact: ArtifactRecord, source: ArtifactRecord) -> bool:
    return (
        artifact.owner.owner_type == source.owner.owner_type
        and artifact.owner.owner_id == source.owner.owner_id
        and artifact.type == source.type
    )
