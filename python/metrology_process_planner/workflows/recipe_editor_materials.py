"""Material action handlers for modeless recipe editing."""

from __future__ import annotations

from dataclasses import replace

from metrology_process_planner.app.command_types import CommandId
from metrology_process_planner.domains.process import Material, ProcessRecipe
from metrology_process_planner.workflows.recipe_editor_material_helpers import (
    material_id_from_action,
    material_usage_step_ids,
    replace_material,
    selected_material,
    unique_material_id,
)
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
    material_id = material_id_from_action(recipe, action_id)
    if not material_id or material_id not in {material.id for material in recipe.materials}:
        return RecipeEditorActionResult(
            "error",
            command_id,
            "Choose a material card before deleting.",
            recipe,
            next_ui_hint="Select a material card and retry.",
        )
    using_steps = material_usage_step_ids(recipe, material_id)
    if using_steps:
        return _blocked_delete(recipe, command_id, material_id, using_steps)
    return _delete_unused_material(recipe, command_id, material_id)


def duplicate_material(
    recipe: ProcessRecipe | None,
    action_id: str,
    command_id: CommandId,
) -> RecipeEditorActionResult:
    """Duplicate a selected material and keep the new card selected."""

    material = selected_material(recipe, action_id, command_id, "duplicating")
    if isinstance(material, RecipeEditorActionResult):
        return material
    current_recipe, source = material
    new_id = unique_material_id(current_recipe, f"{source.id}_copy")
    copied = Material(new_id, f"{source.name} Copy", source.color, source.visible)
    updated = _with_metadata(
        replace(current_recipe, materials=(*current_recipe.materials, copied)),
        dirty=True,
        selected_card_id=f"material:{new_id}",
    )
    return RecipeEditorActionResult(
        "success",
        command_id,
        f"Duplicated material '{source.id}' as '{new_id}'.",
        updated,
        f"material:{new_id}",
        next_ui_hint="Review the duplicated material before saving the recipe.",
    )


def toggle_material_visibility(
    recipe: ProcessRecipe | None,
    action_id: str,
    command_id: CommandId,
) -> RecipeEditorActionResult:
    """Toggle the selected material's render visibility in memory."""

    material = selected_material(recipe, action_id, command_id, "updating")
    if isinstance(material, RecipeEditorActionResult):
        return material
    current_recipe, source = material
    toggled = replace(source, visible=not source.visible)
    updated = replace_material(current_recipe, toggled)
    selected = f"material:{source.id}"
    state = "visible" if toggled.visible else "hidden"
    return RecipeEditorActionResult(
        "success",
        command_id,
        f"Material '{source.id}' is now {state}.",
        _with_metadata(updated, dirty=True, selected_card_id=selected),
        selected,
        next_ui_hint="Recipe previews will use the updated material visibility after refresh.",
    )


def find_material_usage(
    recipe: ProcessRecipe | None,
    action_id: str,
    command_id: CommandId,
) -> RecipeEditorActionResult:
    """Return inline usage information for the selected material."""

    material = selected_material(recipe, action_id, command_id, "finding usage for")
    if isinstance(material, RecipeEditorActionResult):
        return material
    current_recipe, source = material
    using_steps = material_usage_step_ids(current_recipe, source.id)
    if not using_steps:
        message = f"Material '{source.id}' is not used by any process steps."
    else:
        message = f"Material '{source.id}' is used by step(s): {', '.join(using_steps)}."
    return RecipeEditorActionResult(
        "success",
        command_id,
        message,
        current_recipe,
        f"material:{source.id}",
        next_ui_hint="Select a listed process step to inspect or change the reference.",
    )


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


def _with_metadata(recipe: ProcessRecipe, **updates: object) -> ProcessRecipe:
    metadata = dict(recipe.metadata or {})
    metadata.update(updates)
    return replace(recipe, metadata=metadata)
