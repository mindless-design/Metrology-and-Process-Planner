"""Command handlers that delegate session editor actions through the app router."""

from __future__ import annotations

from metrology_process_planner.app.commands import CommandId, CommandRegistry
from metrology_process_planner.app.session_editor import SessionEditorController
from metrology_process_planner.ui.shell import CommandRouteResult
from metrology_process_planner.workflows.editor.view_models import EditorAction, EditorActionType


class SessionEditorCommandService:
    """Translate app-level session commands into editor workflow actions."""

    def __init__(self, controller: SessionEditorController) -> None:
        self._controller = controller

    def save_session_edits(self) -> CommandRouteResult:
        """Save the active editor document through the editor dispatcher."""

        action = EditorAction(EditorActionType.SAVE_EDITS, "Save Edits")
        result = self._controller.dispatch_current_action(action, allow_app_route=False)
        if result is None:
            return CommandRouteResult(
                CommandId.SAVE_SESSION_EDITS,
                "unavailable",
                "No active session editor document is loaded.",
                next_ui_hint="Open or create a session before saving edits.",
            )
        document = result.document
        return CommandRouteResult(
            CommandId.SAVE_SESSION_EDITS,
            result.status,
            result.message,
            updated_document_id=document.session.id,
            selected_item_id=document.selection.selected_item_id,
            next_ui_hint=_save_hint(result.status),
        )


def register_session_editor_command_handlers(
    registry: CommandRegistry,
    controller: SessionEditorController,
) -> None:
    """Register command handlers owned by the unified session editor."""

    service = SessionEditorCommandService(controller)
    registry.register(CommandId.SAVE_SESSION_EDITS, service.save_session_edits)


def _save_hint(status: str) -> str:
    if status == "success":
        return "Session edits are saved."
    if status == "unavailable":
        return "Choose or create a session folder before saving."
    return "Review the editor status strip and diagnostics before retrying save."
