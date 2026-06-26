"""Dispatch helpers for modeless recipe editor actions."""

from __future__ import annotations

from typing import Protocol

from metrology_process_planner.app.command_types import CommandId
from metrology_process_planner.app.recipe_editor_attachment import (
    SessionProvider,
    SessionUpdater,
    attach_recipe_to_session,
)
from metrology_process_planner.app.recipe_editor_controller_support import (
    action_payload,
    discard_payload,
)
from metrology_process_planner.domains.process import ProcessRecipe
from metrology_process_planner.domains.session import ModeRegistry
from metrology_process_planner.workflows.recipe_editor_actions import RecipeEditorActionDispatcher
from metrology_process_planner.workflows.recipe_editor_results import RecipeEditorActionResult


class RecipeEditorDispatchTarget(Protocol):
    """Controller surface needed by recipe editor action dispatch."""

    current_recipe: ProcessRecipe | None
    last_action_result: RecipeEditorActionResult | None
    _active_session_provider: SessionProvider | None
    _active_session_updater: SessionUpdater | None
    _mode_registry: ModeRegistry | None
    _dispatcher: RecipeEditorActionDispatcher

    def close_current(self, force_discard: bool = False) -> RecipeEditorActionResult:
        """Close the current recipe editor surface."""

    def new_current(self, force_discard: bool = False) -> RecipeEditorActionResult:
        """Create a new current recipe."""

    def open_recipe_path(
        self,
        path_text: str,
        force_discard: bool = False,
    ) -> RecipeEditorActionResult:
        """Open a recipe from a path."""

    def save_current(
        self,
        path_override: str = "",
        command_id: CommandId = CommandId.SAVE_RECIPE,
    ) -> RecipeEditorActionResult:
        """Save the current recipe."""

    def open_current(self) -> object:
        """Refresh the modeless recipe editor."""

    def _remember(self, result: RecipeEditorActionResult) -> RecipeEditorActionResult:
        """Store and return the last action result."""


def dispatch_recipe_editor_action(
    controller: RecipeEditorDispatchTarget,
    action_id: str,
) -> RecipeEditorActionResult:
    """Dispatch a recipe editor action against a controller-like object."""

    if action_id.startswith("CloseRecipeEditor"):
        return controller.close_current(force_discard=action_id.endswith(":discard"))
    if action_id.startswith("NewRecipe"):
        return controller.new_current(force_discard=action_id.endswith(":discard"))
    if action_id.startswith("OpenRecipe"):
        force_discard, payload = discard_payload(action_id)
        return controller.open_recipe_path(payload, force_discard)
    if action_id == "SaveRecipe":
        return controller.save_current()
    if action_id.startswith("SaveRecipeAs"):
        return controller.save_current(action_payload(action_id), CommandId.SAVE_RECIPE_AS)
    if action_id == "AttachRecipeToActiveSession":
        result = attach_recipe_to_session(
            controller.current_recipe,
            controller._active_session_provider,
            controller._active_session_updater,
            controller._mode_registry,
        )
        return controller._remember(result)
    result = controller._dispatcher.dispatch(controller.current_recipe, action_id)
    controller.last_action_result = result
    if result.recipe is not None:
        controller.current_recipe = result.recipe
    controller.open_current()
    return result
