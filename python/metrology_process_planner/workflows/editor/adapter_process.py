"""Process-context editor view helpers."""

from __future__ import annotations

from metrology_process_planner.domains.session import SessionRecord, WarningRecord
from metrology_process_planner.workflows.editor.view_models import (
    EditorAction,
    EditorActionType,
    MetadataField,
)


def dashboard_fields(session: SessionRecord) -> tuple[MetadataField, ...]:
    """Return dashboard process-context metadata fields."""

    context = session.process_context
    recipe_status = _recipe_status(session)
    solver_status = _solver_status(session)
    output_counts = _process_output_status_counts(session)
    return (
        MetadataField("session_name", "Session", session.name),
        MetadataField("process_recipe", "Recipe", recipe_status, read_only=True),
        MetadataField("process_solver", "Solver", solver_status, read_only=True),
        MetadataField("render_profile", "Render Profile", context.render_profile or "default"),
        MetadataField("process_outputs", "Process Outputs", output_counts, read_only=True),
        MetadataField(
            "process_warning_count",
            "Process Warnings",
            str(len(_open_process_warnings(session))),
        ),
    )


def process_context_actions(item_id: str) -> tuple[EditorAction, ...]:
    """Return process-context actions for a dashboard or capture item."""

    return (
        EditorAction(EditorActionType.ATTACH_RECIPE, "Attach / Select Recipe", item_id),
        EditorAction(EditorActionType.DETACH_RECIPE, "Detach Recipe", item_id),
        EditorAction(
            EditorActionType.REFRESH_RECIPE_FINGERPRINT,
            "Refresh Recipe Fingerprint",
            item_id,
        ),
        EditorAction(
            EditorActionType.VALIDATE_PROCESS_CONTEXT,
            "Validate Process Context",
            item_id,
        ),
    )


def dashboard_process_context_actions(item_id: str) -> tuple[EditorAction, ...]:
    """Return session-level process-context actions for the dashboard."""

    return process_context_actions(item_id) + (
        EditorAction(
            EditorActionType.REGENERATE_PROCESS_OUTPUT,
            "Regenerate Process Outputs",
            item_id,
        ),
    )


def _process_output_status_counts(session: SessionRecord) -> str:
    counts: dict[str, int] = {}
    for output in session.process_outputs:
        counts[output.status] = counts.get(output.status, 0) + 1
    if not counts:
        return "none"
    return ", ".join(f"{status}:{counts[status]}" for status in sorted(counts))


def _recipe_status(session: SessionRecord) -> str:
    codes = _open_process_warning_codes(session)
    if "PROCESS_RECIPE_FINGERPRINT_MISMATCH" in codes:
        return "mismatch"
    if "PROCESS_RECIPE_FILE_NOT_FOUND" in codes:
        return "missing"
    if "PROCESS_RECIPE_PARSE_FAILED" in codes:
        return "parse_failed"
    context = session.process_context
    if not (context.recipe_id or context.recipe_path or context.recipe_name):
        return "none"
    if context.recipe_path and not context.recipe_fingerprint:
        return "attached_unverified"
    return "attached"


def _solver_status(session: SessionRecord) -> str:
    if "SOLVER_BACKEND_UNAVAILABLE" in _open_process_warning_codes(session):
        return "unavailable"
    status = str((session.process_context.solver_options or {}).get("status", ""))
    if status:
        return status
    return "configured" if session.process_context.solver_backend else "unavailable"


def _open_process_warnings(session: SessionRecord) -> tuple[WarningRecord, ...]:
    return tuple(
        warning
        for warning in session.warnings
        if warning.status == "open"
        and warning.source == "process_context"
        and _warning_is_context_linked(session, warning.id)
    )


def _open_process_warning_codes(session: SessionRecord) -> set[str]:
    return {warning.code for warning in _open_process_warnings(session)}


def _warning_is_context_linked(session: SessionRecord, warning_id: str) -> bool:
    warning_ids = set(session.process_context.warning_ids)
    return not warning_ids or warning_id in warning_ids
