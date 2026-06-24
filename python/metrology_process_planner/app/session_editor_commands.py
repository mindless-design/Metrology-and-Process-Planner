"""Command handlers that delegate session editor actions through the app router."""

from __future__ import annotations

from metrology_process_planner.app.commands import CommandId, CommandRegistry
from metrology_process_planner.app.session_editor import SessionEditorController
from metrology_process_planner.app.session_editor_command_results import (
    action_label,
    command_result,
    no_document,
    selected_pending_is_composite,
)
from metrology_process_planner.ui.shell import CommandRouteResult
from metrology_process_planner.workflows.editor.dispatcher_results import EditorActionResult
from metrology_process_planner.workflows.editor.editing import mark_clean
from metrology_process_planner.workflows.editor.view_models import EditorAction, EditorActionType


class SessionEditorCommandService:
    """Translate app-level session commands into editor workflow actions."""

    def __init__(self, controller: SessionEditorController) -> None:
        self._controller = controller

    def save_session_edits(self) -> CommandRouteResult:
        """Save the active editor document through the editor dispatcher."""

        return _dispatch(
            self._controller,
            CommandId.SAVE_SESSION_EDITS,
            EditorActionType.SAVE_EDITS,
        )

    def discard_unsaved_edits(self) -> CommandRouteResult:
        """Discard in-memory editor edits without touching canonical session files."""

        document = self._controller.current_document
        if document is None:
            return no_document(CommandId.DISCARD_UNSAVED_EDITS, "discarding edits")
        clean = mark_clean(document, document.dirty_state.last_saved_revision)
        self._controller.replace_current_document(clean)
        return command_result(
            CommandId.DISCARD_UNSAVED_EDITS,
            EditorActionResult("success", clean, "Discarded unsaved editor edits."),
        )

    def save_pending_capture(self) -> CommandRouteResult:
        """Save the selected pending capture through the editor workflow."""

        return _dispatch_selected(
            self._controller,
            CommandId.SAVE_PENDING_CAPTURE,
            EditorActionType.PENDING_SAVE,
        )

    def retake_pending_capture(self) -> CommandRouteResult:
        """Retake the selected pending capture through the editor workflow."""

        return _dispatch_selected(
            self._controller,
            CommandId.RETAKE_PENDING_CAPTURE,
            EditorActionType.PENDING_RETAKE,
        )

    def discard_pending_capture(self) -> CommandRouteResult:
        """Discard the selected pending capture through the editor workflow."""

        action_type = EditorActionType.PENDING_DISCARD
        document = self._controller.current_document
        if document is not None and selected_pending_is_composite(document):
            action_type = EditorActionType.COMPOSITE_DISCARD
        return _dispatch_selected(
            self._controller,
            CommandId.DISCARD_PENDING_CAPTURE,
            action_type,
        )

    def save_composite_capture(self) -> CommandRouteResult:
        """Save the selected pending composite through the editor workflow."""

        return _dispatch_selected(
            self._controller,
            CommandId.SAVE_COMPOSITE_CAPTURE,
            EditorActionType.COMPOSITE_SAVE,
        )

    def retake_parent_capture(self) -> CommandRouteResult:
        """Retake the selected composite parent site through the editor workflow."""

        return _dispatch_selected(
            self._controller,
            CommandId.RETAKE_PARENT_CAPTURE,
            EditorActionType.COMPOSITE_RETAKE_PARENT,
        )

    def retake_inner_feature(self) -> CommandRouteResult:
        """Retake the selected composite child feature through the editor workflow."""

        return _dispatch_selected(
            self._controller,
            CommandId.RETAKE_INNER_FEATURE,
            EditorActionType.COMPOSITE_RETAKE_INNER,
        )

    def add_measurement(self) -> CommandRouteResult:
        """Arm measurement capture for the selected saved capture."""

        return _dispatch_selected(
            self._controller,
            CommandId.ADD_MEASUREMENT,
            EditorActionType.ADD_MEASUREMENT,
        )

    def save_measurement(self) -> CommandRouteResult:
        """Save pending measurement edits through the editor workflow."""

        return _dispatch_selected(
            self._controller,
            CommandId.SAVE_MEASUREMENT,
            EditorActionType.SAVE_MEASUREMENT,
        )

    def retake_measurement_line(self) -> CommandRouteResult:
        """Retake the selected pending measurement line."""

        return _dispatch_selected(
            self._controller,
            CommandId.RETAKE_MEASUREMENT_LINE,
            EditorActionType.RETAKE_MEASUREMENT_LINE,
        )

    def discard_measurement(self) -> CommandRouteResult:
        """Discard the selected pending measurement."""

        return _dispatch_selected(
            self._controller,
            CommandId.DISCARD_MEASUREMENT,
            EditorActionType.DISCARD_MEASUREMENT,
        )

    def regenerate_artifact(self) -> CommandRouteResult:
        """Regenerate the selected item's repairable drawing artifact."""

        return _dispatch_selected(
            self._controller,
            CommandId.REGENERATE_ARTIFACT,
            EditorActionType.REGENERATE_ARTIFACT,
        )


def _dispatch_selected(
    controller: SessionEditorController,
    command_id: CommandId,
    action_type: EditorActionType,
) -> CommandRouteResult:
    document = controller.current_document
    if document is None:
        return no_document(command_id, action_label(action_type))
    routed = controller.routed_action
    if routed is not None and routed.action_type is action_type:
        return _dispatch_action(controller, command_id, routed)
    return _dispatch(controller, command_id, action_type, document.selection.selected_item_id)


def _dispatch(
    controller: SessionEditorController,
    command_id: CommandId,
    action_type: EditorActionType,
    item_id: str = "",
) -> CommandRouteResult:
    action = EditorAction(action_type, action_label(action_type), item_id)
    return _dispatch_action(controller, command_id, action)


def _dispatch_action(
    controller: SessionEditorController,
    command_id: CommandId,
    action: EditorAction,
) -> CommandRouteResult:
    result = controller.dispatch_current_action(action, allow_app_route=False)
    if result is None:
        return no_document(command_id, action.label)
    return command_result(command_id, result)


def register_session_editor_command_handlers(
    registry: CommandRegistry,
    controller: SessionEditorController,
) -> None:
    """Register command handlers owned by the unified session editor."""

    from metrology_process_planner.app.session_editor_completion_commands import (
        register_completion_command_handlers,
    )
    from metrology_process_planner.app.session_editor_export_commands import (
        register_export_command_handlers,
    )
    from metrology_process_planner.app.session_editor_process_commands import (
        register_process_editor_command_handlers,
    )

    service = SessionEditorCommandService(controller)
    registry.register(CommandId.SAVE_SESSION_EDITS, service.save_session_edits)
    registry.register(CommandId.DISCARD_UNSAVED_EDITS, service.discard_unsaved_edits)
    registry.register(CommandId.SAVE_PENDING_CAPTURE, service.save_pending_capture)
    registry.register(CommandId.SAVE_COMPOSITE_CAPTURE, service.save_composite_capture)
    registry.register(CommandId.RETAKE_PENDING_CAPTURE, service.retake_pending_capture)
    registry.register(CommandId.RETAKE_PARENT_CAPTURE, service.retake_parent_capture)
    registry.register(CommandId.RETAKE_INNER_FEATURE, service.retake_inner_feature)
    registry.register(CommandId.DISCARD_PENDING_CAPTURE, service.discard_pending_capture)
    registry.register(CommandId.ADD_MEASUREMENT, service.add_measurement)
    registry.register(CommandId.SAVE_MEASUREMENT, service.save_measurement)
    registry.register(CommandId.RETAKE_MEASUREMENT_LINE, service.retake_measurement_line)
    registry.register(CommandId.DISCARD_MEASUREMENT, service.discard_measurement)
    registry.register(CommandId.REGENERATE_ARTIFACT, service.regenerate_artifact)
    register_completion_command_handlers(registry, controller)
    register_export_command_handlers(registry, controller)
    register_process_editor_command_handlers(registry, controller)
