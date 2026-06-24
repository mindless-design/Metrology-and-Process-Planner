"""Validation helpers for process-context workflow state."""

from __future__ import annotations

from pathlib import Path

from metrology_process_planner.domains.session import (
    ArtifactStatus,
    SessionRecord,
    WarningRecord,
)
from metrology_process_planner.workflows.process_capture_extensions import (
    is_process_aware_capture,
    process_extension,
)
from metrology_process_planner.workflows.process_context_support import process_warning


def process_context_warnings(
    session: SessionRecord,
    require_recipe: bool,
) -> tuple[WarningRecord, ...]:
    """Return process-context warnings from canonical session records."""

    return (
        _recipe_warning(session, require_recipe)
        + _solver_warnings(session)
        + _render_profile_warnings(session)
        + _process_capture_warnings(session)
        + _process_output_warnings(session)
    )


def _recipe_warning(session: SessionRecord, require_recipe: bool) -> tuple[WarningRecord, ...]:
    context = session.process_context
    if require_recipe and not (context.recipe_id or context.recipe_path):
        return (
            process_warning(
                "PROCESS_RECIPE_MISSING",
                "No process recipe is attached.",
                "Attach a process recipe and regenerate process outputs.",
            ),
        )
    if context.recipe_path and not Path(context.recipe_path).exists():
        return (
            process_warning(
                "PROCESS_RECIPE_FILE_NOT_FOUND",
                f"Recipe file was not found: {context.recipe_path}",
                "Attach an existing recipe file.",
            ),
        )
    return ()


def _solver_warnings(session: SessionRecord) -> tuple[WarningRecord, ...]:
    if session.process_context.solver_backend:
        return ()
    return (
        process_warning(
            "SOLVER_BACKEND_UNAVAILABLE",
            "No solver backend is configured.",
            "Configure HybridCrossSectionSolver before regenerating process outputs.",
        ),
    )


def _render_profile_warnings(session: SessionRecord) -> tuple[WarningRecord, ...]:
    if session.process_context.render_profile:
        return ()
    if not any(is_process_aware_capture(capture) for capture in session.captures):
        return ()
    return (
        process_warning(
            "RENDER_PROFILE_MISSING",
            "Process-aware captures do not have an active render profile.",
            "Select a render profile before regenerating process outputs.",
        ),
    )


def _process_capture_warnings(session: SessionRecord) -> tuple[WarningRecord, ...]:
    warnings: list[WarningRecord] = []
    for capture in session.captures:
        extension = process_extension(capture)
        if not extension:
            continue
        if extension.get("process_context_ref") != "process_context.active":
            warnings.append(
                process_warning(
                    "PROCESS_RECIPE_MISSING",
                    f"Capture {capture.id} is not linked to process_context.active.",
                    "Relink the capture to the active process context.",
                    capture.id,
                )
            )
    return tuple(warnings)


def _process_output_warnings(session: SessionRecord) -> tuple[WarningRecord, ...]:
    warnings: list[WarningRecord] = []
    stale_artifact_owner_ids = {
        artifact.owner.owner_id
        for artifact in (session.artifacts or {}).values()
        if artifact.type == "process_output" and artifact.status is ArtifactStatus.STALE
    }
    for output in session.process_outputs:
        capture_id = str(dict(output.metadata or {}).get("capture_id", ""))
        if output.status == "stale" or capture_id in stale_artifact_owner_ids:
            warnings.append(
                process_warning(
                    "PROCESS_OUTPUT_STALE",
                    f"Process output {output.id} is stale.",
                    "Regenerate process outputs.",
                    capture_id,
                )
            )
    return tuple(warnings)
