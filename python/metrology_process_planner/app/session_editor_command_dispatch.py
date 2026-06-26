"""Shared dispatch helpers for session editor command handlers."""

from __future__ import annotations

from metrology_process_planner.app.commands import CommandId
from metrology_process_planner.app.session_editor import SessionEditorController
from metrology_process_planner.app.session_editor_command_results import (
    action_label,
    command_result,
    no_document,
)
from metrology_process_planner.app.session_editor_models import SessionEditorOpenResult
from metrology_process_planner.ui.shell import CommandRouteResult
from metrology_process_planner.workflows.editor.view_models import EditorAction, EditorActionType


def dispatch_selected_editor_action(
    controller: SessionEditorController,
    command_id: CommandId,
    action_type: EditorActionType,
) -> CommandRouteResult:
    """Dispatch a selected editor item action without app rerouting."""

    document = controller.current_document
    if document is None:
        return no_document(command_id, action_label(action_type))
    routed = controller.routed_action
    if routed is not None and routed.action_type is action_type:
        return dispatch_editor_action(controller, command_id, routed)
    return dispatch_editor_action(
        controller,
        command_id,
        EditorAction(
            action_type,
            action_label(action_type),
            document.selection.selected_item_id,
        ),
    )


def dispatch_editor_action(
    controller: SessionEditorController,
    command_id: CommandId,
    action: EditorAction,
) -> CommandRouteResult:
    """Dispatch an explicit editor action without routing it back through the app."""

    result = controller.dispatch_current_action(action, allow_app_route=False)
    if result is None:
        return no_document(command_id, action.label)
    return command_result(command_id, result)


def open_result(command_id: CommandId, result: SessionEditorOpenResult) -> CommandRouteResult:
    """Convert a session editor open/save/close result to a command route result."""

    document = result.document
    return CommandRouteResult(
        command_id,
        result.status,
        result.message,
        updated_document_id=document.session.id if document is not None else "",
        selected_item_id=document.selection.selected_item_id if document is not None else "",
    )
