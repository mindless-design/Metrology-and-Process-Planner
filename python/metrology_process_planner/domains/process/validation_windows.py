"""Process-window structured validation helpers."""

from __future__ import annotations

from metrology_process_planner.domains.process.steps import ProcessWindow
from metrology_process_planner.domains.process.validation_messages import (
    RecipeValidationMessage,
    recipe_validation_message,
)


def window_messages(windows: tuple[ProcessWindow, ...]) -> tuple[RecipeValidationMessage, ...]:
    """Return structured validation messages for process windows."""

    return tuple(
        recipe_validation_message(
            f"window-{window.name}-{index}",
            "error",
            "process_window",
            f"Window {window.name}: {warning}",
            repair="Set lower <= target <= upper.",
        )
        for window in windows
        for index, warning in enumerate(window.validate())
    )
