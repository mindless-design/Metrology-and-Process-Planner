"""Setup item action helpers for the unified editor."""

from __future__ import annotations

from metrology_process_planner.workflows.editor.adapter_artifact_actions import (
    artifact_repair_actions,
)
from metrology_process_planner.workflows.editor.document import SessionItem
from metrology_process_planner.workflows.editor.view_models import EditorAction, EditorActionType


def setup_actions(item: SessionItem) -> tuple[EditorAction, ...]:
    """Return modeless actions for the selected setup navigator item."""

    return (
        EditorAction(EditorActionType.REOPEN_SETUP, "Reopen Setup", item.item_id),
        *artifact_repair_actions(item, "Regenerate Setup Artifact"),
    )
