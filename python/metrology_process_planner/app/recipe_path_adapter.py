"""Operator path selection contracts for recipe editor commands."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Protocol


@dataclass(frozen=True)
class RecipePathSelection:
    """Result from an operator recipe JSON picker."""

    path: Path | None = None
    status: str = "unavailable"
    message: str = "Recipe path picker is not connected."

    @classmethod
    def selected(cls, path: str | Path) -> RecipePathSelection:
        """Return a successful recipe path selection."""

        return cls(Path(path), "selected", "Recipe path selected.")


class RecipePathAdapter(Protocol):
    """Boundary implemented by UI/KLayout shells for recipe JSON paths."""

    def select_open_recipe(self) -> RecipePathSelection:
        """Return an existing recipe JSON file."""

    def select_save_recipe_as(self) -> RecipePathSelection:
        """Return a destination recipe JSON file."""

    def select_attach_recipe(self) -> RecipePathSelection:
        """Return an existing recipe JSON file to attach to the active session."""


class UnavailableRecipePathAdapter:
    """Default adapter for hosts that have not supplied recipe picker UI yet."""

    def select_open_recipe(self) -> RecipePathSelection:
        """Report that open-recipe picker UI is not connected."""

        return RecipePathSelection(
            status="unavailable",
            message="Open Recipe requires a recipe JSON picker.",
        )

    def select_save_recipe_as(self) -> RecipePathSelection:
        """Report that save-recipe-as picker UI is not connected."""

        return RecipePathSelection(
            status="unavailable",
            message="Save Recipe As requires a recipe destination picker.",
        )

    def select_attach_recipe(self) -> RecipePathSelection:
        """Report that attach-recipe picker UI is not connected."""

        return RecipePathSelection(
            status="unavailable",
            message="Attach Recipe requires a recipe JSON picker.",
        )
