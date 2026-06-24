"""Modeless recipe preview action workflows."""

from __future__ import annotations

from dataclasses import replace

from metrology_process_planner.app.command_types import CommandId
from metrology_process_planner.domains.process import ProcessRecipe
from metrology_process_planner.workflows.recipe_editor_results import RecipeEditorActionResult


def preview_recipe(
    recipe: ProcessRecipe | None,
    action_id: str,
    command_id: CommandId,
) -> RecipeEditorActionResult:
    """Record the requested preview scope without invoking solver backends."""

    if recipe is None:
        return RecipeEditorActionResult(
            "unavailable",
            command_id,
            "Open or create a recipe before previewing.",
            next_ui_hint="Use Open Recipe or New Recipe first.",
        )
    step_id = _step_id(action_id) if command_id is CommandId.PREVIEW_RECIPE_THROUGH_STEP else ""
    if step_id and step_id not in {step.id for step in recipe.steps}:
        return RecipeEditorActionResult(
            "error",
            command_id,
            f"Process step '{step_id}' was not found for preview.",
            recipe,
            next_ui_hint="Select an existing process step and retry preview.",
        )
    updated = _with_preview_metadata(recipe, step_id)
    return RecipeEditorActionResult(
        "warning",
        command_id,
        _preview_message(step_id),
        updated,
        f"step:{step_id}" if step_id else "",
        ("recipe-preview-backend-unavailable",),
        "Recipe preview state is recorded; connect a preview backend to render frames.",
    )


def _step_id(action_id: str) -> str:
    if ":" not in action_id:
        return ""
    return action_id.split(":", 1)[1]


def _with_preview_metadata(recipe: ProcessRecipe, step_id: str) -> ProcessRecipe:
    metadata = dict(recipe.metadata or {})
    metadata["preview_scope"] = "through_step" if step_id else "full_recipe"
    metadata["selected_step_id"] = step_id
    if step_id:
        metadata["selected_card_id"] = f"step:{step_id}"
    return replace(recipe, metadata=metadata)


def _preview_message(step_id: str) -> str:
    if step_id:
        return f"Preview through step '{step_id}' is waiting for a preview backend."
    return "Full recipe preview is waiting for a preview backend."
