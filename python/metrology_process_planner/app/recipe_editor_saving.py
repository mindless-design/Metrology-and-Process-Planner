"""Save-result helpers for the modeless recipe editor."""

from __future__ import annotations

from dataclasses import dataclass, replace
from pathlib import Path

from metrology_process_planner.app.command_types import CommandId
from metrology_process_planner.domains.process import ProcessRecipe
from metrology_process_planner.persistence.recipe_store import ProcessRecipeJsonStore
from metrology_process_planner.workflows.recipe_editor_results import RecipeEditorActionResult


@dataclass(frozen=True)
class RecipeSaveOutcome:
    """Result plus updated recipe after a recipe save attempt."""

    result: RecipeEditorActionResult
    recipe: ProcessRecipe | None = None


def save_recipe(
    recipe: ProcessRecipe | None,
    store: ProcessRecipeJsonStore,
    command_id: CommandId,
    path_override: str = "",
) -> RecipeSaveOutcome:
    """Save a recipe to its current path or a provided Save As path."""

    if recipe is None:
        return _unavailable_no_recipe(command_id)
    recipe_path = _save_path(recipe, path_override)
    if recipe_path is None:
        return _unavailable_no_path(recipe, command_id)
    try:
        saved_path = store.save(recipe, recipe_path)
    except OSError as exc:
        return _save_error(recipe, command_id, exc)
    saved = _mark_saved(recipe, saved_path)
    return RecipeSaveOutcome(
        RecipeEditorActionResult(
            "success",
            command_id,
            f"Recipe saved: {saved_path}",
            saved,
            next_ui_hint="Continue editing or return to the session editor.",
        ),
        saved,
    )


def _unavailable_no_recipe(command_id: CommandId) -> RecipeSaveOutcome:
    return RecipeSaveOutcome(
        RecipeEditorActionResult(
            "unavailable",
            command_id,
            "No recipe is loaded.",
            next_ui_hint="Open or create a recipe before saving.",
        ),
    )


def _unavailable_no_path(
    recipe: ProcessRecipe,
    command_id: CommandId,
) -> RecipeSaveOutcome:
    return RecipeSaveOutcome(
        RecipeEditorActionResult(
            "unavailable",
            command_id,
            "Recipe has no save path.",
            recipe,
            next_ui_hint="Use Save As before saving this recipe.",
        ),
        recipe,
    )


def _save_error(
    recipe: ProcessRecipe,
    command_id: CommandId,
    exc: OSError,
) -> RecipeSaveOutcome:
    return RecipeSaveOutcome(
        RecipeEditorActionResult(
            "error",
            command_id,
            f"Recipe save failed: {exc}",
            recipe,
            next_ui_hint="Fix the recipe path or permissions and retry Save.",
        ),
        recipe,
    )


def _save_path(recipe: ProcessRecipe, path_override: str) -> Path | None:
    if path_override:
        return Path(path_override)
    value = dict(recipe.metadata or {}).get("recipe_path", "")
    if not value:
        return None
    return Path(str(value))


def _mark_saved(recipe: ProcessRecipe, saved_path: Path) -> ProcessRecipe:
    metadata = dict(recipe.metadata or {})
    metadata.pop("dirty", None)
    metadata["recipe_path"] = str(saved_path)
    return replace(recipe, metadata=metadata)
