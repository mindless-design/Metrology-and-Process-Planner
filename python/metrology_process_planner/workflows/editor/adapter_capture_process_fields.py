"""Capture process metadata fields for the editor adapter."""

from __future__ import annotations

from metrology_process_planner.domains.session import CaptureRecord, ModeRegistry, SessionRecord
from metrology_process_planner.workflows.editor.builder_basics import mode_is_process_aware
from metrology_process_planner.workflows.editor.view_models import MetadataField
from metrology_process_planner.workflows.process_capture_extensions import process_solver_request


def capture_process_fields(
    session: SessionRecord,
    capture: CaptureRecord,
    mode_registry: ModeRegistry | None = None,
) -> tuple[MetadataField, ...]:
    """Return process-context metadata for a saved capture."""

    if not mode_is_process_aware(session, mode_registry):
        return ()
    process = _capture_process_extension(capture)
    if not process:
        return ()
    recipe = session.process_context.recipe_name or session.process_context.recipe_id or "none"
    return (
        MetadataField("process_recipe", "Recipe", recipe, read_only=True),
        MetadataField(
            "solver_operation",
            "Solver Operation",
            str(process.get("solver_operation", "")),
            read_only=True,
        ),
        MetadataField(
            "process_window",
            "Process Window",
            str(process.get("process_window", "")),
            read_only=True,
        ),
        MetadataField(
            "process_outputs",
            "Process Outputs",
            _capture_output_statuses(session, capture.id),
            read_only=True,
        ),
        MetadataField("process_warnings", "Warnings", str(len(capture.warning_ids))),
    )


def _capture_process_extension(capture: CaptureRecord) -> dict[str, object]:
    solver = process_solver_request(capture)
    if not solver:
        return {}
    return {
        "solver_operation": solver.get("operation", ""),
        "process_window": solver.get("process_window_variant", ""),
    }


def _capture_output_statuses(session: SessionRecord, capture_id: str) -> str:
    statuses = [
        output.status
        for output in session.process_outputs
        if dict(output.metadata or {}).get("capture_id") == capture_id
    ]
    if not statuses:
        return "none"
    counts = {status: statuses.count(status) for status in set(statuses)}
    return ", ".join(f"{status}:{counts[status]}" for status in sorted(counts))
