"""Shared material helpers for recipe editor workflows."""

from __future__ import annotations

from dataclasses import replace

from metrology_process_planner.app.command_types import CommandId
from metrology_process_planner.domains.process import Material, ProcessRecipe, ProcessStep
from metrology_process_planner.workflows.recipe_editor_results import RecipeEditorActionResult


def material_id_from_action(recipe: ProcessRecipe, action_id: str) -> str:
    """Return the target material ID from an action or selected card."""

    if ":" in action_id:
        return action_id.split(":", 1)[1]
    selected = str(dict(recipe.metadata or {}).get("selected_card_id", ""))
    if selected.startswith("material:"):
        return selected.removeprefix("material:")
    return ""


def selected_material(
    recipe: ProcessRecipe | None,
    action_id: str,
    command_id: CommandId,
    verb: str,
) -> tuple[ProcessRecipe, Material] | RecipeEditorActionResult:
    """Resolve the action target material or return an inline error result."""

    if recipe is None:
        return RecipeEditorActionResult(
            "unavailable",
            command_id,
            f"Open or create a recipe before {verb} materials.",
            next_ui_hint="Use Open Recipe or New Recipe first.",
        )
    material_id = material_id_from_action(recipe, action_id)
    material = next((item for item in recipe.materials if item.id == material_id), None)
    if material is None:
        return RecipeEditorActionResult(
            "error",
            command_id,
            "Choose a material card first.",
            recipe,
            next_ui_hint="Select a material card and retry.",
        )
    return recipe, material


def unique_material_id(recipe: ProcessRecipe, base: str) -> str:
    """Return a material ID that does not collide with the recipe library."""

    existing = {material.id for material in recipe.materials}
    material_id = base
    index = 2
    while material_id in existing:
        material_id = f"{base}_{index}"
        index += 1
    return material_id


def replace_material(recipe: ProcessRecipe, replacement: Material) -> ProcessRecipe:
    """Return a recipe with one material replaced by ID."""

    return replace(
        recipe,
        materials=tuple(
            replacement if material.id == replacement.id else material
            for material in recipe.materials
        ),
    )


def material_usage_step_ids(recipe: ProcessRecipe, material_id: str) -> tuple[str, ...]:
    """Return process step IDs that reference a material."""

    return tuple(step.id for step in recipe.steps if material_id in step_material_ids(step))


def step_material_ids(step: ProcessStep) -> tuple[str, ...]:
    """Return all material IDs referenced by one process step."""

    return tuple(
        item
        for item in (
            step.material_id,
            *step.target_material_ids,
            *step.stop_material_ids,
        )
        if item
    )
