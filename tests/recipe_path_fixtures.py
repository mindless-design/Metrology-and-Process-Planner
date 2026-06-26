"""Recipe path adapter fakes for app command tests."""

from __future__ import annotations

from metrology_process_planner.app.recipe_path_adapter import RecipePathSelection


class FakeRecipePathAdapter:
    """Fake operator recipe path adapter for command tests."""

    def __init__(
        self,
        open_recipe: RecipePathSelection | None = None,
        save_as: RecipePathSelection | None = None,
        attach_recipe: RecipePathSelection | None = None,
    ) -> None:
        self._open_recipe = open_recipe
        self._save_as = save_as
        self._attach_recipe = attach_recipe

    def select_open_recipe(self) -> RecipePathSelection:
        """Return the configured open-recipe path."""

        return self._open_recipe or RecipePathSelection()

    def select_save_recipe_as(self) -> RecipePathSelection:
        """Return the configured save-as recipe path."""

        return self._save_as or RecipePathSelection()

    def select_attach_recipe(self) -> RecipePathSelection:
        """Return the configured attach-recipe path."""

        return self._attach_recipe or RecipePathSelection()
