"""Shared route-result helpers for session document commands."""

from __future__ import annotations

from metrology_process_planner.app.commands import CommandId
from metrology_process_planner.app.session_editor_models import SessionEditorOpenResult
from metrology_process_planner.ui.shell import CommandRouteResult


def open_result(command_id: CommandId, result: SessionEditorOpenResult) -> CommandRouteResult:
    """Convert a session editor open/save result into a route result."""

    document = result.document
    return CommandRouteResult(
        command_id,
        result.status,
        result.message,
        updated_document_id=document.session.id if document is not None else "",
        selected_item_id=document.selection.selected_item_id if document is not None else "",
    )


def selection_result(command_id: CommandId, status: str, message: str) -> CommandRouteResult:
    """Convert picker status into a non-mutating route result."""

    if status == "selected":
        status = "error"
    if status == "cancelled":
        return CommandRouteResult(
            command_id,
            "cancelled",
            message,
            next_ui_hint="No session document was changed.",
        )
    return CommandRouteResult(
        command_id,
        "unavailable",
        message,
        next_ui_hint="Connect a platform picker adapter and retry the command.",
    )
