"""Header view models for the modeless recipe editor."""

from __future__ import annotations

from metrology_process_planner.domains.process import ProcessRecipe
from metrology_process_planner.ui.recipe_editor.view_models import RecipeHeaderViewModel
from metrology_process_planner.ui.shell.view_models import EditorActionViewModel


def header_model(recipe: ProcessRecipe | None) -> RecipeHeaderViewModel:
    """Return recipe header status without requiring widget-side inference."""

    if recipe is None:
        return RecipeHeaderViewModel("", "No recipe loaded")
    metadata = dict(recipe.metadata or {})
    warning_count = len(recipe.validate())
    dirty = bool(metadata.get("dirty", False))
    recipe_path = str(metadata.get("recipe_path", ""))
    return RecipeHeaderViewModel(
        recipe.id,
        recipe.name,
        recipe_path,
        dirty,
        "warning" if warning_count else "valid",
        warning_count,
        _attachment_status(recipe_path, dirty),
        _status_text(dirty, warning_count, recipe_path),
    )


def header_actions(recipe: ProcessRecipe | None) -> tuple[EditorActionViewModel, ...]:
    """Return command-shaped recipe editor header actions with disabled reasons."""

    loaded = recipe is not None
    metadata = dict(recipe.metadata or {}) if recipe is not None else {}
    recipe_path = str(metadata.get("recipe_path", ""))
    dirty = bool(metadata.get("dirty", False))
    return (
        EditorActionViewModel("NewRecipe", "New Recipe"),
        EditorActionViewModel("OpenRecipe", "Open Recipe"),
        _action("SaveRecipe", "Save", loaded and bool(recipe_path), _save_reason(loaded)),
        _action("SaveRecipeAs", "Save As", loaded, _loaded_reason(loaded)),
        _action("ValidateRecipe", "Validate", loaded, _loaded_reason(loaded)),
        _action("PreviewRecipe", "Preview Build", loaded, _loaded_reason(loaded)),
        _action(
            "AttachRecipeToActiveSession",
            "Attach to Active Session",
            loaded and bool(recipe_path) and not dirty,
            _attach_reason(loaded, recipe_path, dirty),
        ),
        EditorActionViewModel("CloseRecipeEditor", "Close"),
    )


def _action(
    action_id: str,
    label: str,
    enabled: bool,
    disabled_reason: str,
) -> EditorActionViewModel:
    return EditorActionViewModel(action_id, label, enabled=enabled, disabled_reason=disabled_reason)


def _attachment_status(recipe_path: str, dirty: bool) -> str:
    if not recipe_path:
        return "unsaved"
    return "dirty" if dirty else "ready_to_attach"


def _status_text(dirty: bool, warning_count: int, recipe_path: str) -> str:
    if dirty:
        return "Unsaved recipe edits."
    if warning_count:
        return f"{warning_count} validation warning(s)."
    if not recipe_path:
        return "Recipe has not been saved to a file yet."
    return "Recipe is ready."


def _loaded_reason(loaded: bool) -> str:
    return "" if loaded else "Load or create a recipe first."


def _save_reason(loaded: bool) -> str:
    if not loaded:
        return "Load or create a recipe before saving."
    return "Use Save As before Save for a new recipe."


def _attach_reason(loaded: bool, recipe_path: str, dirty: bool) -> str:
    if not loaded:
        return "Load or create a recipe before attaching it."
    if dirty:
        return "Save the recipe before attaching it."
    if not recipe_path:
        return "Save the recipe before attaching it."
    return ""


__all__ = ["header_actions", "header_model"]
