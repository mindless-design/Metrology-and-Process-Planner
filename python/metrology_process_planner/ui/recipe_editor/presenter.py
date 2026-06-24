"""Presenter for the recipe editor workflow surface."""

from __future__ import annotations

from metrology_process_planner.domains.process import ProcessRecipe
from metrology_process_planner.ui.shell import (
    MetadataFieldViewModel,
    RecipeEditorViewModel,
    SessionNavigatorItem,
    WarningViewModel,
)


class RecipeEditorPresenter:
    """Build recipe editor view models from process recipes."""

    def build(self, recipe: ProcessRecipe | None) -> RecipeEditorViewModel:
        """Return the recipe editor view model."""

        if recipe is None:
            return RecipeEditorViewModel(
                "",
                "No recipe loaded",
                (),
                (),
                (WarningViewModel("recipe-unloaded", "info", "No recipe is loaded."),),
            )
        return RecipeEditorViewModel(
            recipe.id,
            recipe.name,
            _sections(recipe),
            (
                MetadataFieldViewModel("name", "Name", recipe.name, required=True),
                MetadataFieldViewModel("material_count", "Materials", str(len(recipe.materials))),
                MetadataFieldViewModel("step_count", "Steps", str(len(recipe.steps))),
            ),
            tuple(
                WarningViewModel(f"recipe-warning-{index}", "warning", warning)
                for index, warning in enumerate(recipe.validate(), start=1)
            ),
        )


def _sections(recipe: ProcessRecipe) -> tuple[SessionNavigatorItem, ...]:
    return (
        SessionNavigatorItem("materials", "Materials", "recipe_section"),
        SessionNavigatorItem("steps", "Steps", "recipe_section"),
        SessionNavigatorItem("process_windows", "Process Windows", "recipe_section"),
        SessionNavigatorItem("summary", recipe.name, "recipe_summary"),
    )
