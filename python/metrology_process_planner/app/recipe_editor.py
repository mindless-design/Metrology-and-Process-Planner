"""Application controller for the recipe editor surface."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from metrology_process_planner.app.command_types import CommandId
from metrology_process_planner.app.recipe_editor_attachment import (
    SessionProvider,
    SessionUpdater,
)
from metrology_process_planner.app.recipe_editor_controller_support import (
    is_dirty,
    recipe_id,
    window_title,
)
from metrology_process_planner.app.recipe_editor_dispatch import dispatch_recipe_editor_action
from metrology_process_planner.app.recipe_editor_opening import (
    dirty_switch_block,
    new_recipe,
    open_recipe,
)
from metrology_process_planner.app.recipe_editor_path_actions import (
    open_path_or_result,
    save_path_or_result,
)
from metrology_process_planner.app.recipe_editor_saving import save_recipe
from metrology_process_planner.app.recipe_path_adapter import (
    RecipePathAdapter,
    UnavailableRecipePathAdapter,
)
from metrology_process_planner.app.window_registry import WindowOpenStatus, WindowRegistry
from metrology_process_planner.domains.process import ProcessRecipe
from metrology_process_planner.domains.session import ModeRegistry
from metrology_process_planner.persistence.recipe_store import ProcessRecipeJsonStore
from metrology_process_planner.ui.modeless import (
    InMemoryModelessSurfaceFactory,
    ModelessSurfaceShell,
)
from metrology_process_planner.ui.recipe_editor import RecipeEditorPresenter
from metrology_process_planner.ui.recipe_editor.view_models import RecipeEditorViewModel
from metrology_process_planner.workflows.recipe_editor_actions import RecipeEditorActionDispatcher
from metrology_process_planner.workflows.recipe_editor_results import RecipeEditorActionResult


@dataclass(frozen=True)
class RecipeEditorOpenResult:
    """Result of opening or refreshing the recipe editor."""

    status: str
    view_model: RecipeEditorViewModel
    message: str = ""
    window: Any | None = None


class RecipeEditorController:
    """Resolve recipe editor commands without saving recipe files directly."""

    def __init__(
        self,
        presenter: RecipeEditorPresenter | None = None,
        dispatcher: RecipeEditorActionDispatcher | None = None,
        recipe_store: ProcessRecipeJsonStore | None = None,
        shell: ModelessSurfaceShell | None = None,
        window_registry: WindowRegistry[Any] | None = None,
        active_session_provider: SessionProvider | None = None,
        active_session_updater: SessionUpdater | None = None,
        recipe_path_adapter: RecipePathAdapter | None = None,
        mode_registry: ModeRegistry | None = None,
    ) -> None:
        self._presenter = presenter if presenter is not None else RecipeEditorPresenter()
        self._dispatcher = dispatcher if dispatcher is not None else RecipeEditorActionDispatcher()
        self._recipe_store = recipe_store if recipe_store is not None else ProcessRecipeJsonStore()
        self._shell = shell or ModelessSurfaceShell(InMemoryModelessSurfaceFactory())
        self._window_registry = window_registry if window_registry is not None else WindowRegistry()
        self._active_session_provider = active_session_provider
        self._active_session_updater = active_session_updater
        self._recipe_path_adapter = recipe_path_adapter or UnavailableRecipePathAdapter()
        self._mode_registry = mode_registry
        self.current_recipe: ProcessRecipe | None = None
        self.last_action_result: RecipeEditorActionResult | None = None

    def set_recipe(self, recipe: ProcessRecipe | None) -> None:
        """Store the recipe that subsequent editor actions should operate on."""
        self.current_recipe = recipe

    def open_current(self) -> RecipeEditorOpenResult:
        """Return a recipe editor view model for the current recipe."""
        view_model = self._presenter.build(self.current_recipe)
        registry_result = self._window_registry.get_or_create_recipe_editor(
            recipe_id(self.current_recipe),
            window_title(view_model),
            lambda: self._shell.open(window_title(view_model), view_model),
            refresh_existing=lambda surface: self._shell.render(surface, view_model),
        )
        if registry_result.status is WindowOpenStatus.FAILED:
            return RecipeEditorOpenResult("failed", view_model, registry_result.message)
        if isinstance(registry_result.window, dict):
            registry_result.window["on_action"] = self.dispatch_action
        status = "opened" if self.current_recipe is not None else "unavailable"
        if registry_result.status is WindowOpenStatus.RAISED:
            status = "raised"
        return RecipeEditorOpenResult(status, view_model, window=registry_result.window)

    def dispatch_action(self, action_id: str) -> RecipeEditorActionResult:
        """Route one modeless recipe action through controller-owned services."""
        return dispatch_recipe_editor_action(self, action_id)

    def close_current(self, force_discard: bool = False) -> RecipeEditorActionResult:
        """Close the modeless recipe editor or block on unsaved edits."""
        if is_dirty(self.current_recipe) and not force_discard:
            result = RecipeEditorActionResult(
                "blocked",
                CommandId.CLOSE_RECIPE_EDITOR,
                "Recipe has unsaved edits.",
                self.current_recipe,
                next_ui_hint="Save the recipe or confirm discard before closing.",
            )
            self.last_action_result = result
            return result
        self._window_registry.close(f"recipe-editor:{recipe_id(self.current_recipe)}")
        message = "Recipe editor closed."
        if force_discard:
            message = "Recipe editor closed and unsaved edits were discarded."
        result = RecipeEditorActionResult(
            "success",
            CommandId.CLOSE_RECIPE_EDITOR,
            message,
            self.current_recipe,
            next_ui_hint="Return to the session editor when ready.",
        )
        self.last_action_result = result
        return result

    def new_current(self, force_discard: bool = False) -> RecipeEditorActionResult:
        """Create a new in-memory recipe or block on unsaved edits."""
        recipe = self.current_recipe
        if is_dirty(recipe) and not force_discard and recipe is not None:
            return self._remember(dirty_switch_block(CommandId.NEW_RECIPE, recipe))
        return _replace_current(self, new_recipe())

    def open_recipe_path(
        self,
        path_text: str,
        force_discard: bool = False,
    ) -> RecipeEditorActionResult:
        """Open a recipe path or block on unsaved edits."""
        recipe = self.current_recipe
        if is_dirty(recipe) and not force_discard and recipe is not None:
            return self._remember(dirty_switch_block(CommandId.OPEN_RECIPE, recipe))
        selected = open_path_or_result(self._recipe_path_adapter, path_text)
        if isinstance(selected, RecipeEditorActionResult):
            return self._remember(selected)
        return _replace_current(self, open_recipe(selected, self._recipe_store))

    def save_current(
        self,
        path_override: str = "",
        command_id: CommandId = CommandId.SAVE_RECIPE,
    ) -> RecipeEditorActionResult:
        """Save the current recipe and refresh the modeless window on success."""
        selected = save_path_or_result(
            self._recipe_path_adapter,
            self.current_recipe,
            command_id,
            path_override,
        )
        if isinstance(selected, RecipeEditorActionResult):
            return self._remember(selected)
        outcome = save_recipe(
            self.current_recipe,
            self._recipe_store,
            command_id,
            selected,
        )
        if outcome.recipe is not None:
            self.current_recipe = outcome.recipe
        if outcome.result.status == "success":
            self.open_current()
        return self._remember(outcome.result)

    def _remember(self, result: RecipeEditorActionResult) -> RecipeEditorActionResult:
        self.last_action_result = result
        return result


def _replace_current(
    controller: RecipeEditorController,
    result: RecipeEditorActionResult,
) -> RecipeEditorActionResult:
    if result.recipe is not None:
        controller._window_registry.close(f"recipe-editor:{recipe_id(controller.current_recipe)}")
        controller.current_recipe = result.recipe
        controller.open_current()
    return controller._remember(result)
