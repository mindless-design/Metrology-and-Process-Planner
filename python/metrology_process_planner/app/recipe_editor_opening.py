"""Open/new helpers for the modeless recipe editor."""

from __future__ import annotations

from dataclasses import replace
from pathlib import Path

from metrology_process_planner.app.command_types import CommandId
from metrology_process_planner.domains.process import (
    Material,
    ProcessRecipe,
    ProcessStep,
    ProcessStepKind,
)
from metrology_process_planner.persistence.recipe_store import ProcessRecipeJsonStore
from metrology_process_planner.workflows.recipe_editor_results import RecipeEditorActionResult


def new_recipe() -> RecipeEditorActionResult:
    """Create a starter recipe for modeless editing."""

    recipe = ProcessRecipe(
        "untitled-recipe",
        "Untitled Recipe",
        (Material("si", "Silicon", "#aaaaaa"),),
        (ProcessStep("substrate", ProcessStepKind.SUBSTRATE, "si"),),
        metadata={"dirty": True, "selected_card_id": "material:si"},
    )
    return RecipeEditorActionResult(
        "success",
        CommandId.NEW_RECIPE,
        "Created a new process recipe.",
        recipe,
        "material:si",
        next_ui_hint="Edit the starter material and substrate step, then Save As.",
    )


def open_recipe(path_text: str, store: ProcessRecipeJsonStore) -> RecipeEditorActionResult:
    """Load a process recipe from a path-bearing command."""

    if not path_text:
        return RecipeEditorActionResult(
            "unavailable",
            CommandId.OPEN_RECIPE,
            "No recipe path was provided.",
            next_ui_hint="Choose a recipe JSON file before opening.",
        )
    path = Path(path_text)
    try:
        loaded = store.load(path)
    except (OSError, ValueError) as exc:
        return RecipeEditorActionResult(
            "error",
            CommandId.OPEN_RECIPE,
            f"Recipe open failed: {exc}",
            next_ui_hint="Choose another recipe JSON file or repair the selected file.",
        )
    recipe = _opened_recipe(loaded, path)
    return RecipeEditorActionResult(
        "success",
        CommandId.OPEN_RECIPE,
        f"Opened recipe: {path}",
        recipe,
        str(dict(recipe.metadata or {}).get("selected_card_id", "")),
        next_ui_hint="Review the recipe or attach it to the active session.",
    )


def dirty_switch_block(command_id: CommandId, recipe: ProcessRecipe) -> RecipeEditorActionResult:
    """Return a modeless blocked result before replacing a dirty recipe."""

    return RecipeEditorActionResult(
        "blocked",
        command_id,
        "Recipe has unsaved edits.",
        recipe,
        next_ui_hint="Save the current recipe or confirm discard before switching recipes.",
    )


def _opened_recipe(recipe: ProcessRecipe, path: Path) -> ProcessRecipe:
    metadata = dict(recipe.metadata or {})
    metadata.pop("dirty", None)
    metadata["recipe_path"] = str(path)
    metadata.setdefault("selected_card_id", _default_card(recipe))
    return replace(recipe, metadata=metadata)


def _default_card(recipe: ProcessRecipe) -> str:
    if recipe.materials:
        return f"material:{recipe.materials[0].id}"
    if recipe.steps:
        return f"step:{recipe.steps[0].id}"
    return ""
