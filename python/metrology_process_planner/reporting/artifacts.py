"""Register generated reports as session artifacts."""

from __future__ import annotations

from dataclasses import replace
from pathlib import Path

from metrology_process_planner.domains.session import (
    ArtifactDependencyRef,
    ArtifactOwnerRef,
    ArtifactRecord,
    ArtifactRepairMetadata,
    ArtifactStatus,
    ReportRecord,
    SessionRecord,
    ModeRegistry,
)
from metrology_process_planner.reporting.backends import ExportedReport
from metrology_process_planner.reporting.models import ReportDocument
from metrology_process_planner.workflows.artifacts.signatures import current_signature

_ARTIFACT_TYPES = {
    "pptx": "powerpoint_deck",
    "pdf": "pdf_report",
    "csv": "csv_export",
    "images.zip": "image_bundle",
    "manifest": "report_manifest",
}


class ReportArtifactRegistrar:
    """Add generated report artifacts to canonical session records."""

    def register(
        self,
        session: SessionRecord,
        document: ReportDocument,
        exported: ExportedReport,
        session_folder: Path,
        mode_registry: ModeRegistry | None = None,
    ) -> SessionRecord:
        """Return a session copy with generated report artifacts recorded."""

        report_id = document.metadata.report_id
        artifacts = _supersede_report_artifacts(session, report_id)
        output_artifacts = _output_artifacts(
            session,
            document,
            exported,
            session_folder,
            mode_registry,
        )
        artifacts.update({artifact.id: artifact for artifact in output_artifacts})
        reports = tuple(
            report for report in session.reports if report.id != report_id
        ) + (_report_record(document, output_artifacts),)
        return replace(session, artifacts=artifacts, reports=reports)


def _supersede_report_artifacts(
    session: SessionRecord,
    report_id: str,
) -> dict[str, ArtifactRecord]:
    artifacts: dict[str, ArtifactRecord] = {}
    for artifact_id, artifact in (session.artifacts or {}).items():
        if artifact.owner.owner_type == "report" and artifact.owner.owner_id == report_id:
            artifacts[artifact_id] = replace(artifact, status=ArtifactStatus.SUPERSEDED)
        else:
            artifacts[artifact_id] = artifact
    return artifacts


def _output_artifacts(
    session: SessionRecord,
    document: ReportDocument,
    exported: ExportedReport,
    session_folder: Path,
    mode_registry: ModeRegistry | None,
) -> tuple[ArtifactRecord, ...]:
    owner = ArtifactOwnerRef("report", document.metadata.report_id, "report_output")
    records = [
        _artifact(
            session,
            document,
            "manifest",
            exported.manifest_path,
            session_folder,
            owner,
            mode_registry,
        )
    ]
    for format_name, path in exported.outputs.items():
        records.append(
            _artifact(
                session,
                document,
                format_name,
                path,
                session_folder,
                owner,
                mode_registry,
            )
        )
    return tuple(records)


def _artifact(
    session: SessionRecord,
    document: ReportDocument,
    format_name: str,
    path: Path,
    session_folder: Path,
    owner: ArtifactOwnerRef,
    mode_registry: ModeRegistry | None,
) -> ArtifactRecord:
    artifact_id = f"{document.metadata.report_id}-{format_name.replace('.', '-')}"
    return ArtifactRecord(
        artifact_id,
        _ARTIFACT_TYPES.get(format_name, "report_artifact"),
        f"{document.metadata.title} {format_name}",
        _relative_path(path, session_folder),
        owner,
        status=ArtifactStatus.PRESENT,
        dependencies=(
            ArtifactDependencyRef(
                kind="session_data",
                id=session.id,
                signature=current_signature(session, "session_data", "", mode_registry),
            ),
        ),
        generator=_generator(format_name),
        repair=ArtifactRepairMetadata(
            repair_action="rebuild_report",
            repair_suggestion="Rebuild the report from current session data.",
            regenerable=True,
        ),
    )


def _report_record(
    document: ReportDocument,
    artifacts: tuple[ArtifactRecord, ...],
) -> ReportRecord:
    return ReportRecord(
        document.metadata.report_id,
        document.metadata.title,
        document.metadata.template_id,
        artifact_refs={artifact.type: artifact.id for artifact in artifacts},
        warning_ids=tuple(warning.warning_id for warning in document.warnings),
    )


def _relative_path(path: Path, session_folder: Path) -> str:
    try:
        return path.resolve().relative_to(session_folder.resolve()).as_posix()
    except ValueError:
        return path.as_posix()


def _generator(format_name: str) -> str:
    if format_name == "pptx":
        return "powerpoint_export"
    return "report_export"
