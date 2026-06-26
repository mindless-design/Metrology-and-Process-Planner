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

    def take_another_measurement(self) -> CommandRouteResult:
        """Apply the allowed take-another-measurement prompt choice."""

        return apply_completion_choice_to_controller(
            self._controller,
            CommandId.TAKE_ANOTHER_MEASUREMENT,
            MeasurementCompletionChoice.TAKE_ANOTHER,
            "take another measurement",
        )

    def done(self) -> CommandRouteResult:
        """Apply the allowed post-measurement done prompt choice."""

        return apply_completion_choice_to_controller(
            self._controller,
            CommandId.DONE,
            MeasurementCompletionChoice.DONE,
            "complete measurement workflow",
        )


def apply_completion_choice_to_controller(
    controller: SessionEditorController,
    command_id: CommandId,
    choice: MeasurementCompletionChoice,
    action_text: str,
) -> CommandRouteResult:
    """Apply one measurement-completion choice to the active editor document."""

    document = controller.current_document
    if document is None:
        return no_document(command_id, action_text)
    result = apply_measurement_completion_choice(document.session, choice)
    rebuilt = SessionDocumentBuilder(mode_registry=controller.mode_registry).build(
        result.session,
        raw_payload=document.raw_payload,
    )
    if result.selected_item_id:
        rebuilt = select_item(rebuilt, result.selected_item_id)
    controller.replace_current_document(rebuilt)
    return CommandRouteResult(
        command_id,
        result.status,
        result.message,
        updated_document_id=rebuilt.session.id,
        selected_item_id=rebuilt.selection.selected_item_id,
        next_ui_hint=_next_hint(result.status, choice),
    )


def register_completion_command_handlers(
    registry: CommandRegistry,
    controller: SessionEditorController,
) -> None:
    """Register post-measurement completion command handlers."""

    service = SessionEditorCompletionCommandService(controller)
    registry.register(CommandId.TAKE_ANOTHER_MEASUREMENT, service.take_another_measurement)
    registry.register(CommandId.DONE, service.done)


def _next_hint(status: str, choice: MeasurementCompletionChoice) -> str:
    if status == "success" and choice is MeasurementCompletionChoice.TAKE_ANOTHER:
        return "Draw another measurement line inside the active capture."
    if status == "success":
        return "Measurement workflow is complete."
    return "Save a measurement before choosing another measurement."
