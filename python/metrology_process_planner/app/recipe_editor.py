"""Application controller for the recipe editor surface."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from metrology_process_planner.app.window_registry import WindowOpenStatus, WindowRegistry
from metrology_process_planner.domains.process import ProcessRecipe
from metrology_process_planner.ui.modeless import (
    InMemoryModelessSurfaceFactory,
    ModelessSurfaceShell,
)
from metrology_process_planner.ui.recipe_editor import RecipeEditorPresenter
from metrology_process_planner.ui.recipe_editor.view_models import RecipeEditorViewModel
from metrology_process_planner.workflows.recipe_editor_actions import (
    RecipeEditorActionDispatcher,
    RecipeEditorActionResult,
)


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
        shell: ModelessSurfaceShell | None = None,
        window_registry: WindowRegistry[Any] | None = None,
    ) -> None:
        self._presenter = presenter if presenter is not None else RecipeEditorPresenter()
        self._dispatcher = dispatcher if dispatcher is not None else RecipeEditorActionDispatcher()
        self._shell = shell or ModelessSurfaceShell(InMemoryModelessSurfaceFactory())
        self._window_registry = window_registry if window_registry is not None else WindowRegistry()
        self.current_recipe: ProcessRecipe | None = None
        self.last_action_result: RecipeEditorActionResult | None = None

    def set_recipe(self, recipe: ProcessRecipe | None) -> None:
        """Set the recipe currently shown by the editor."""

        self.current_recipe = recipe

    def open_current(self) -> RecipeEditorOpenResult:
        """Return a recipe editor view model for the current recipe."""

        view_model = self._presenter.build(self.current_recipe)
        registry_result = self._window_registry.open_or_raise(
            _window_key(self.current_recipe),
            _window_title(view_model),
            lambda: self._shell.open(_window_title(view_model), view_model),
            refresh_existing=lambda window: self._shell.render(window, view_model),
        )
        if registry_result.status is WindowOpenStatus.FAILED:
            return RecipeEditorOpenResult("failed", view_model, registry_result.message)
        status = _status(registry_result.status, self.current_recipe)
        return RecipeEditorOpenResult(status, view_model, window=registry_result.window)

    def dispatch_action(self, action_id: str) -> RecipeEditorActionResult:
        """Dispatch a recipe editor action and refresh the modeless window."""

        result = self._dispatcher.dispatch(self.current_recipe, action_id)
        self.last_action_result = result
        if result.recipe is not None:
            self.current_recipe = result.recipe
        self.open_current()
        return result


def _window_key(recipe: ProcessRecipe | None) -> str:
    recipe_id = recipe.id if recipe is not None else "no-recipe"
    return f"recipe-editor:{recipe_id}"


def _window_title(view_model: RecipeEditorViewModel) -> str:
    return f"Recipe Editor - {view_model.title}"


def _status(status: WindowOpenStatus, recipe: ProcessRecipe | None) -> str:
    if status is WindowOpenStatus.RAISED:
        return "raised"
    return "opened" if recipe is not None else "unavailable"
