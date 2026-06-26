"""Result contracts for modeless recipe editor actions."""

from __future__ import annotations

from dataclasses import dataclass

from metrology_process_planner.domains.commands import CommandId
from metrology_process_planner.domains.process import ProcessRecipe


@dataclass(frozen=True)
class RecipeEditorActionResult:
    """Result from one recipe editor action intent."""

    status: str
    command_id: CommandId | None = None
    message: str = ""
    recipe: ProcessRecipe | None = None
    selected_card_id: str = ""
    warning_ids: tuple[str, ...] = ()
    next_ui_hint: str = ""
