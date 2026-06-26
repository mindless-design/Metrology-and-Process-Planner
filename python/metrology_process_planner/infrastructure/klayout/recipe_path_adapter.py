"""KLayout picker adapter for recipe JSON paths."""

from __future__ import annotations

from typing import Any

from metrology_process_planner.app.recipe_path_adapter import RecipePathSelection


class KLayoutRecipePathAdapter:
    """Collect recipe paths from KLayout/Qt dialogs."""

    def __init__(self, pya_module: Any) -> None:
        self._pya = pya_module

    def select_open_recipe(self) -> RecipePathSelection:
        """Ask for an existing recipe JSON file."""

        path = _open_file(self._pya, "Open Process Recipe", "Recipe JSON (*.json)")
        if not path:
            return RecipePathSelection(status="cancelled", message="Open Recipe cancelled.")
        return RecipePathSelection.selected(path)

    def select_save_recipe_as(self) -> RecipePathSelection:
        """Ask for a destination recipe JSON path."""

        path = _save_file(self._pya, "Save Process Recipe As", "Recipe JSON (*.json)")
        if not path:
            return RecipePathSelection(status="cancelled", message="Save Recipe As cancelled.")
        return RecipePathSelection.selected(path)

    def select_attach_recipe(self) -> RecipePathSelection:
        """Ask for an existing recipe JSON file to attach."""

        path = _open_file(self._pya, "Attach Process Recipe", "Recipe JSON (*.json)")
        if not path:
            return RecipePathSelection(status="cancelled", message="Attach Recipe cancelled.")
        return RecipePathSelection.selected(path)


def _open_file(pya: Any, title: str, filter_text: str) -> str:
    dialog = getattr(pya, "QFileDialog", None)
    if dialog is None or not hasattr(dialog, "getOpenFileName"):
        return ""
    return _first_path(dialog.getOpenFileName(None, title, "", filter_text))


def _save_file(pya: Any, title: str, filter_text: str) -> str:
    dialog = getattr(pya, "QFileDialog", None)
    if dialog is None or not hasattr(dialog, "getSaveFileName"):
        return ""
    return _first_path(dialog.getSaveFileName(None, title, "recipe.json", filter_text))


def _first_path(result: Any) -> str:
    if isinstance(result, tuple):
        return str(result[0]) if result and result[0] else ""
    return str(result) if result else ""
