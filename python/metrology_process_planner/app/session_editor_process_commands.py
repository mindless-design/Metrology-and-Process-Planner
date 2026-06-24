"""Process-context command handlers for the active session editor."""

from __future__ import annotations

from metrology_process_planner.app.commands import CommandId, CommandRegistry
from metrology_process_planner.app.session_editor import SessionEditorController
from metrology_process_planner.app.session_editor_commands import _dispatch_selected
from metrology_process_planner.ui.shell import CommandRouteResult
from metrology_process_planner.workflows.editor.view_models import EditorActionType


class SessionEditorProcessCommandService:
    """Translate process command intents into editor workflow actions."""

    def __init__(self, controller: SessionEditorController) -> None:
        self._controller = controller

    def attach_recipe(self) -> CommandRouteResult:
        """Attach a recipe path supplied by the current editor action payload."""

        return _dispatch_selected(
            self._controller,
            CommandId.ATTACH_RECIPE,
            EditorActionType.ATTACH_RECIPE,
        )

    def detach_recipe(self) -> CommandRouteResult:
        """Detach the active recipe from the current editor session."""

        return _dispatch_selected(
            self._controller,
            CommandId.DETACH_RECIPE,
            EditorActionType.DETACH_RECIPE,
        )

    def validate_process_context(self) -> CommandRouteResult:
        """Validate the active session process context."""

        return _dispatch_selected(
            self._controller,
            CommandId.VALIDATE_PROCESS_CONTEXT,
            EditorActionType.VALIDATE_PROCESS_CONTEXT,
        )

    def regenerate_process_output(self) -> CommandRouteResult:
        """Regenerate process outputs for the selected item or dashboard."""

        return _dispatch_selected(
            self._controller,
            CommandId.REGENERATE_PROCESS_OUTPUT,
            EditorActionType.REGENERATE_PROCESS_OUTPUT,
        )


def register_process_editor_command_handlers(
    registry: CommandRegistry,
    controller: SessionEditorController,
) -> None:
    """Register process-context command handlers for the active editor."""

    service = SessionEditorProcessCommandService(controller)
    registry.register(CommandId.ATTACH_RECIPE, service.attach_recipe)
    registry.register(CommandId.DETACH_RECIPE, service.detach_recipe)
    registry.register(CommandId.VALIDATE_PROCESS_CONTEXT, service.validate_process_context)
    registry.register(CommandId.REGENERATE_PROCESS_OUTPUT, service.regenerate_process_output)
