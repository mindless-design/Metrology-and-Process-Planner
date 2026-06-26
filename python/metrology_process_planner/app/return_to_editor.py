"""Return-to-editor command routing helpers."""

from __future__ import annotations

from metrology_process_planner.app.bootstrap_models import UiControllers
from metrology_process_planner.app.commands import CommandId
from metrology_process_planner.app.session_editor import SessionEditorController
from metrology_process_planner.app.session_editor_completion_commands import (
    apply_completion_choice_to_controller,
)
from metrology_process_planner.workflows.measurement_completion import (
    MeasurementCompletionChoice,
)


def return_to_editor(ui: UiControllers) -> object:
    """Apply measurement completion return when active, otherwise open the editor."""

    result = apply_completion_choice_to_controller(
        ui.session_editor,
        CommandId.RETURN_TO_EDITOR,
        MeasurementCompletionChoice.RETURN_TO_EDITOR,
        "return to editor",
    )
    if result.status == "success":
        return result
    open_session_editor(ui.session_editor)
    return result


def open_session_editor(controller: SessionEditorController) -> None:
    """Open or raise the active session editor."""

    controller.open_current_session()
