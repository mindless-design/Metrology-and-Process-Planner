"""Material action handlers for modeless recipe editing."""

from __future__ import annotations

from dataclasses import replace

from metrology_process_planner.app.command_types import CommandId
from metrology_process_planner.domains.process import ProcessRecipe, ProcessStep
from metrology_process_planner.workflows.recipe_editor_results import RecipeEditorActionResult


def delete_material(
    recipe: ProcessRecipe | None,
    action_id: str,
    command_id: CommandId,
) -> RecipeEditorActionResult:
    """Delete an unused material or block deletion with an inline result."""

    if recipe is None:
        return RecipeEditorActionResult(
            "unavailable",
            command_id,
            "Open or create a recipe before deleting materials.",
            next_ui_hint="Use Open Recipe or New Recipe first.",
        )
    material_id = _material_id_from_action(recipe, action_id)
    if not material_id or material_id not in {material.id for material in recipe.materials}:
        return RecipeEditorActionResult(
            "error",
            command_id,
            "Choose a material card before deleting.",
            recipe,
            next_ui_hint="Select a material card and retry.",
        )
    using_steps = _material_usage_step_ids(recipe, material_id)
    if using_steps:
        return _blocked_delete(recipe, command_id, material_id, using_steps)
    return _delete_unused_material(recipe, command_id, material_id)


def _blocked_delete(
    recipe: ProcessRecipe,
    command_id: CommandId,
    material_id: str,
    using_steps: tuple[str, ...],
) -> RecipeEditorActionResult:
    return RecipeEditorActionResult(
        "blocked",
        command_id,
        f"Material '{material_id}' is used by step(s): {', '.join(using_steps)}.",
        recipe,
        f"material:{material_id}",
        (f"recipe-material-in-use-{material_id}",),
        "Remove or replace those step references before deleting the material.",
    )


def _delete_unused_material(
    recipe: ProcessRecipe,
    command_id: CommandId,
    material_id: str,
) -> RecipeEditorActionResult:
    updated = _with_metadata(
        replace(
            recipe,
            materials=tuple(
                material for material in recipe.materials if material.id != material_id
            ),
        ),
        dirty=True,
        selected_card_id="",
    )
    return RecipeEditorActionResult(
        "success",
        command_id,
        f"Deleted material '{material_id}'.",
        updated,
        next_ui_hint="Review the material list before saving the recipe.",
    )


def _material_id_from_action(recipe: ProcessRecipe, action_id: str) -> str:
    if ":" in action_id:
        return action_id.split(":", 1)[1]
    selected = str(dict(recipe.metadata or {}).get("selected_card_id", ""))
    if selected.startswith("material:"):
        return selected.removeprefix("material:")
    return ""


def _material_usage_step_ids(recipe: ProcessRecipe, material_id: str) -> tuple[str, ...]:
    return tuple(step.id for step in recipe.steps if material_id in _step_material_ids(step))


def _step_material_ids(step: ProcessStep) -> tuple[str, ...]:
    return tuple(
        item
        for item in (
            step.material_id,
            *step.target_material_ids,
            *step.stop_material_ids,
        )
        if item
    )


def _with_metadata(recipe: ProcessRecipe, **updates: object) -> ProcessRecipe:
    metadata = dict(recipe.metadata or {})
    metadata.update(updates)
    return replace(recipe, metadata=metadata)
