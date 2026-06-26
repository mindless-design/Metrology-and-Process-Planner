"""Deterministic pure-Python operator workflow lab for process sessions."""

from __future__ import annotations

from dataclasses import dataclass, replace
from pathlib import Path
from typing import Any

from metrology_process_planner.domains.geometry import Box
from metrology_process_planner.domains.session import (
    ArtifactStatus,
    ProcessContext,
    SessionRecord,
)
from metrology_process_planner.persistence.json_store import SessionJsonStore
from metrology_process_planner.persistence.paths import SessionPaths
from metrology_process_planner.persistence.process_output_store import ProcessOutputStore
from metrology_process_planner.reporting.requests import ReportRequest
from metrology_process_planner.reporting.service import ReportGenerationService
from metrology_process_planner.workflows.artifacts import ArtifactRepairService
from metrology_process_planner.workflows.editor.builder import SessionDocumentBuilder
from metrology_process_planner.workflows.process_context import (
    attach_recipe,
    regenerate_process_outputs,
)
from metrology_process_planner.workflows.process_context_models import (
    AttachRecipeCommand,
    RegenerateProcessOutputsCommand,
)
from tests.synthetic_operator_lab_builders import (
    base_operator_session,
    point_capture,
    profile_capture,
    source_artifacts,
)
from tests.synthetic_operator_lab_summaries import (
    report_sections,
    sorted_artifacts,
    summarize_session,
    write_gallery_manifest,
)
from tests.synthetic_process_lab import RECIPE_ROOT


@dataclass(frozen=True)
class OperatorLabResult:
    """Result bundle returned by a synthetic operator run."""

    session: SessionRecord
    paths: SessionPaths
    summary: dict[str, Any]
    report_sections: tuple[str, ...]
    gallery_manifest_path: Path | None = None


def run_happy_path(folder: Path) -> OperatorLabResult:
    """Create a complete synthetic process session and artifacts."""

    paths = SessionPaths.for_folder(folder)
    paths.ensure_created()
    session = attach_recipe(
        base_operator_session("synthetic-operator-session"),
        AttachRecipeCommand(str(RECIPE_ROOT / "profilometry_surface_recipe.json")),
    ).session
    session = replace(
        session,
        captures=(profile_capture("cap-profile-001"), point_capture("cap-point-001")),
        artifacts=source_artifacts(),
    )
    session = regenerate_process_outputs(
        session,
        RegenerateProcessOutputsCommand("", solver_available=True),
    ).session
    repair = ArtifactRepairService()
    session = _repair_process_artifacts(session, paths, repair)
    session, _scan = repair.scan_session(session, paths)
    session = _generate_report(session, paths)
    SessionJsonStore().save(session, paths)
    manifest = write_gallery_manifest(session, paths, "synthetic_operator_lab")
    return OperatorLabResult(
        session,
        paths,
        summarize_session(session),
        report_sections(session),
        manifest,
    )


def run_missing_recipe_path(folder: Path) -> OperatorLabResult:
    """Exercise placeholder output generation when the recipe path is missing."""

    paths = SessionPaths.for_folder(folder)
    paths.ensure_created()
    session = replace(
        base_operator_session("synthetic-missing-recipe"),
        process_context=ProcessContext(
            recipe_path=str(folder / "does-not-exist.json"),
            solver_backend="HybridCrossSectionSolver",
            render_profile="default_cross_section",
        ),
        captures=(profile_capture("cap-profile-001"),),
    )
    result = regenerate_process_outputs(
        session,
        RegenerateProcessOutputsCommand("", solver_available=True),
    )
    session, _scan = ArtifactRepairService().scan_session(result.session, paths)
    SessionJsonStore().save(session, paths)
    return OperatorLabResult(session, paths, summarize_session(session), ())


def run_missing_source_artifact(folder: Path) -> OperatorLabResult:
    """Create a valid report with a missing source visual placeholder."""

    result = run_happy_path(folder)
    source = result.session.artifacts["source-site-image"]
    artifacts = {
        **dict(result.session.artifacts or {}),
        source.id: replace(source, status=ArtifactStatus.MISSING, warning_ids=()),
    }
    session = replace(result.session, artifacts=artifacts)
    session, _scan = ArtifactRepairService().scan_session(session, result.paths)
    session = _generate_report(session, result.paths)
    SessionJsonStore().save(session, result.paths)
    return OperatorLabResult(
        session,
        result.paths,
        summarize_session(session),
        report_sections(session),
    )


def run_changed_geometry_scan(folder: Path) -> OperatorLabResult:
    """Modify capture geometry after report generation and rescan for stale outputs."""

    result = run_happy_path(folder)
    capture = result.session.captures[0]
    bounds = capture.geometry.bounds
    assert bounds is not None
    changed = replace(
        capture,
        geometry=replace(
            capture.geometry,
            bounds=Box(bounds.left, bounds.bottom, bounds.right + 1.0, bounds.top),
        ),
    )
    session = replace(result.session, captures=(changed,) + result.session.captures[1:])
    session, _scan = ArtifactRepairService().scan_session(session, result.paths)
    SessionJsonStore().save(session, result.paths)
    return OperatorLabResult(session, result.paths, summarize_session(session), ())


def _generate_report(session: SessionRecord, paths: SessionPaths) -> SessionRecord:
    document = SessionDocumentBuilder().build(session)
    request = ReportRequest(
        session.id,
        "process_review",
        output_formats=("pptx", "pdf", "csv", "images.zip"),
    )
    result = ReportGenerationService().generate(document, request, paths.folder)
    if result.updated_session is None:
        raise AssertionError(f"Report generation failed: {result.message}")
    return result.updated_session


def _repair_process_artifacts(
    session: SessionRecord,
    paths: SessionPaths,
    repair: ArtifactRepairService,
) -> SessionRecord:
    visual_roles = {"profile_image", "cross_section_image", "stack_image", "process_flow_frame"}
    current = session
    for artifact in sorted_artifacts(current):
        if artifact.owner.role in visual_roles and artifact.status is ArtifactStatus.STALE:
            current = repair.repair_artifact(current, artifact.id, paths)
    return ProcessOutputStore().export_ready_outputs(paths, current)
