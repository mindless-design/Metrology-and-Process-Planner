"""Application controller for the recipe editor surface."""

from __future__ import annotations

from dataclasses import dataclass

from metrology_process_planner.domains.process import ProcessRecipe
from metrology_process_planner.ui.recipe_editor import RecipeEditorPresenter
from metrology_process_planner.ui.recipe_editor.view_models import RecipeEditorViewModel


@dataclass(frozen=True)
class RecipeEditorOpenResult:
    """Result of opening or refreshing the recipe editor."""

    status: str
    view_model: RecipeEditorViewModel
    message: str = ""


class RecipeEditorController:
    """Resolve recipe editor commands without saving recipe files directly."""

    def __init__(self, presenter: RecipeEditorPresenter | None = None) -> None:
        self._presenter = presenter if presenter is not None else RecipeEditorPresenter()
        self.current_recipe: ProcessRecipe | None = None

    def set_recipe(self, recipe: ProcessRecipe | None) -> None:
        """Set the recipe currently shown by the editor."""

        self.current_recipe = recipe

    def open_current(self) -> RecipeEditorOpenResult:
        """Return a recipe editor view model for the current recipe."""

        view_model = self._presenter.build(self.current_recipe)
        status = "opened" if self.current_recipe is not None else "unavailable"
        return RecipeEditorOpenResult(status, view_model)
