"""Post-measurement completion command handlers for the session editor."""

from __future__ import annotations

from metrology_process_planner.app.commands import CommandId, CommandRegistry
from metrology_process_planner.app.session_editor import SessionEditorController
from metrology_process_planner.app.session_editor_command_results import no_document
from metrology_process_planner.ui.shell import CommandRouteResult
from metrology_process_planner.workflows.editor import SessionDocumentBuilder, select_item
from metrology_process_planner.workflows.measurement_completion import (
    MeasurementCompletionChoice,
    apply_measurement_completion_choice,
)


class SessionEditorCompletionCommandService:
    """Apply post-measurement prompt choices to the active editor document."""

    def __init__(self, controller: SessionEditorController) -> None:
        self._controller = controller
        self._builder = SessionDocumentBuilder()

    def take_another_measurement(self) -> CommandRouteResult:
        """Apply the allowed take-another-measurement prompt choice."""

        document = self._controller.current_document
        if document is None:
            return no_document(CommandId.TAKE_ANOTHER_MEASUREMENT, "take another measurement")
        result = apply_measurement_completion_choice(
            document.session,
            MeasurementCompletionChoice.TAKE_ANOTHER,
        )
        rebuilt = self._builder.build(result.session, raw_payload=document.raw_payload)
        if result.selected_item_id:
            rebuilt = select_item(rebuilt, result.selected_item_id)
        self._controller.replace_current_document(rebuilt)
        return CommandRouteResult(
            CommandId.TAKE_ANOTHER_MEASUREMENT,
            result.status,
            result.message,
            updated_document_id=rebuilt.session.id,
            selected_item_id=rebuilt.selection.selected_item_id,
            next_ui_hint=_next_hint(result.status),
        )


def register_completion_command_handlers(
    registry: CommandRegistry,
    controller: SessionEditorController,
) -> None:
    """Register post-measurement completion command handlers."""

    service = SessionEditorCompletionCommandService(controller)
    registry.register(CommandId.TAKE_ANOTHER_MEASUREMENT, service.take_another_measurement)


def _next_hint(status: str) -> str:
    if status == "success":
        return "Draw another measurement line inside the active capture."
    return "Save a measurement before choosing another measurement."
