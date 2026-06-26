"""Support helpers for app-level session editor command results."""

from __future__ import annotations

from metrology_process_planner.app.commands import CommandId
from metrology_process_planner.ui.shell import CommandRouteResult
from metrology_process_planner.workflows.editor.dispatcher_results import EditorActionResult
from metrology_process_planner.workflows.editor.document import SessionDocument
from metrology_process_planner.workflows.editor.view_models import EditorActionType


def no_document(command_id: CommandId, action_label: str) -> CommandRouteResult:
    """Return a structured unavailable result when no editor document is active."""

    return CommandRouteResult(
        command_id,
        "unavailable",
        f"No active session editor document is loaded for {action_label}.",
        next_ui_hint="Open or create a session before using this command.",
    )


def command_result(command_id: CommandId, result: EditorActionResult) -> CommandRouteResult:
    """Convert an editor action result into an app command result."""

    document = result.document
    return CommandRouteResult(
        command_id,
        result.status,
        result.message,
        updated_document_id=document.session.id,
        selected_item_id=document.selection.selected_item_id,
        next_ui_hint=_next_hint(command_id, result.status),
        output_path=str(result.output_path or ""),
        post_action_prompt=result.post_action_prompt,
    )


def action_label(action_type: EditorActionType) -> str:
    """Return a compact user-facing fallback label for an editor action."""

    return action_type.value.replace("_", " ")


def selected_pending_is_composite(document: SessionDocument) -> bool:
    """Return whether the selected pending item stores compound metadata."""

    selected = document.items_by_id.get(document.selection.selected_item_id)
    if selected is None or selected.record_ref is None:
        return False
    if selected.record_ref.record_type != "pending_capture":
        return False
    pending_id = selected.record_ref.record_id
    for pending in document.session.pending_captures:
        if pending.id == pending_id:
            return bool(dict(pending.metadata or {}).get("compound"))
    return False


def _next_hint(command_id: CommandId, status: str) -> str:
    if command_id is CommandId.SAVE_SESSION_EDITS:
        return _save_hint(status)
    if status == "success":
        return "Session editor command completed."
    if status == "unavailable":
        return "Select an item that supports this command."
    return "Review the editor status strip and diagnostics before retrying."


def _save_hint(status: str) -> str:
    if status == "success":
        return "Session edits are saved."
    if status == "unavailable":
        return "Choose or create a session folder before saving."
    return "Review the editor status strip and diagnostics before retrying save."
