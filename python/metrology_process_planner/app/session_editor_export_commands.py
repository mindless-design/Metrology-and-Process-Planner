"""Export and shell-handoff command handlers for the session editor."""

from __future__ import annotations

from metrology_process_planner.app.commands import CommandId, CommandRegistry
from metrology_process_planner.app.session_editor import SessionEditorController
from metrology_process_planner.app.session_editor_command_dispatch import (
    dispatch_selected_editor_action as _dispatch_selected,
)
from metrology_process_planner.ui.shell import CommandRouteResult
from metrology_process_planner.workflows.editor.view_models import EditorActionType


class SessionEditorExportCommandService:
    """Translate export and path handoff commands into editor actions."""

    def __init__(self, controller: SessionEditorController) -> None:
        self._controller = controller

    def export_csv(self) -> CommandRouteResult:
        """Export capture CSV for the active editor document."""

        return _dispatch_selected(
            self._controller,
            CommandId.EXPORT_CSV,
            EditorActionType.EXPORT_CSV,
        )

    def open_output_folder(self) -> CommandRouteResult:
        """Resolve the active session output folder for the UI shell."""

        return _dispatch_selected(
            self._controller,
            CommandId.OPEN_OUTPUT_FOLDER,
            EditorActionType.OPEN_OUTPUT_FOLDER,
        )


def register_export_command_handlers(
    registry: CommandRegistry,
    controller: SessionEditorController,
) -> None:
    """Register export and shell-handoff command handlers."""

    service = SessionEditorExportCommandService(controller)
    registry.register(CommandId.EXPORT_CSV, service.export_csv)
    registry.register(CommandId.OPEN_OUTPUT_FOLDER, service.open_output_folder)
