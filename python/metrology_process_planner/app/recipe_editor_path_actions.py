"""Path-picker helpers for modeless recipe-editor commands."""

from __future__ import annotations

from metrology_process_planner.app.command_types import CommandId
from metrology_process_planner.app.recipe_path_adapter import RecipePathAdapter
from metrology_process_planner.domains.process import ProcessRecipe
from metrology_process_planner.workflows.recipe_editor_results import RecipeEditorActionResult


def selected_recipe_path(
    adapter: RecipePathAdapter,
    command_id: CommandId,
    recipe: ProcessRecipe | None = None,
) -> str | RecipeEditorActionResult:
    """Return a selected recipe path or a modeless picker result."""

    selection = (
        adapter.select_save_recipe_as()
        if command_id is CommandId.SAVE_RECIPE_AS
        else adapter.select_open_recipe()
    )
    if selection.status == "selected" and selection.path is not None:
        return str(selection.path)
    return RecipeEditorActionResult(
        selection.status,
        command_id,
        selection.message,
        recipe,
        next_ui_hint="No recipe file was changed.",
    )


def open_path_or_result(
    adapter: RecipePathAdapter,
    path_text: str,
) -> str | RecipeEditorActionResult:
    """Return an explicit open path or ask the host adapter for one."""

    if path_text:
        return path_text
    return selected_recipe_path(adapter, CommandId.OPEN_RECIPE)


def save_path_or_result(
    adapter: RecipePathAdapter,
    recipe: ProcessRecipe | None,
    command_id: CommandId,
    path_override: str,
) -> str | RecipeEditorActionResult:
    """Return an explicit save path or ask the host adapter for Save As."""

    if command_id is not CommandId.SAVE_RECIPE_AS or path_override:
        return path_override
    no_recipe = save_as_no_recipe_result(recipe)
    if no_recipe is not None:
        return no_recipe
    return selected_recipe_path(adapter, command_id, recipe)


def save_as_no_recipe_result(recipe: ProcessRecipe | None) -> RecipeEditorActionResult | None:
    """Return unavailable before opening a save dialog without a loaded recipe."""

    if recipe is not None:
        return None
    return RecipeEditorActionResult(
        "unavailable",
        CommandId.SAVE_RECIPE_AS,
        "No recipe is loaded.",
        recipe,
        next_ui_hint="Create or open a recipe before saving.",
    )
