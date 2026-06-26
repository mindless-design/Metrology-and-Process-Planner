"""Process-context editor action helpers."""

from __future__ import annotations

from metrology_process_planner.workflows.editor.adapter_dashboard_fields import dashboard_fields
from metrology_process_planner.workflows.editor.view_models import EditorAction, EditorActionType

__all__ = ("dashboard_fields", "dashboard_process_context_actions", "process_context_actions")


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
