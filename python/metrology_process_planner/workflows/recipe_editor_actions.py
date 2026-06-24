"""Command-shaped recipe editor action dispatch."""

from __future__ import annotations

from dataclasses import replace

from metrology_process_planner.app.command_types import CommandId
from metrology_process_planner.app.commands import command_id_from_view_action
from metrology_process_planner.domains.process import (
    ProcessRecipe,
    ProcessStep,
    ProcessStepKind,
)
from metrology_process_planner.workflows.recipe_editor_material_edits import edit_material
from metrology_process_planner.workflows.recipe_editor_materials import (
    add_material,
    delete_material,
    duplicate_material,
    find_material_usage,
    toggle_material_visibility,
)
from metrology_process_planner.workflows.recipe_editor_preview import preview_recipe
from metrology_process_planner.workflows.recipe_editor_results import RecipeEditorActionResult
from metrology_process_planner.workflows.recipe_editor_step_edits import edit_step
from metrology_process_planner.workflows.recipe_editor_steps import (
    delete_step,
    duplicate_step,
    move_step,
    set_step_enabled,
)


class RecipeEditorActionDispatcher:
    """Apply safe recipe editor actions without direct file persistence."""

    def dispatch(
        self,
        recipe: ProcessRecipe | None,
        action_id: str,
    ) -> RecipeEditorActionResult:
        """Dispatch one recipe editor action ID."""

        if action_id.startswith("SelectRecipeCard:"):
            return _select_card(recipe, action_id.split(":", 1)[1])
        try:
            command_id = command_id_from_view_action(action_id)
        except ValueError:
            return RecipeEditorActionResult(
                "error",
                message=f"Unknown recipe editor action: {action_id}",
                recipe=recipe,
                next_ui_hint="Open diagnostics and review the recipe editor action.",
            )
        if command_id is CommandId.ADD_PROCESS_STEP:
            return _add_step_template(recipe, action_id, command_id)
        material_result = _dispatch_material_action(recipe, action_id, command_id)
        if material_result is not None:
            return material_result
        if command_id is CommandId.DUPLICATE_PROCESS_STEP:
            return duplicate_step(recipe, action_id, command_id)
        if command_id is CommandId.DELETE_PROCESS_STEP:
            return delete_step(recipe, action_id, command_id)
        if command_id is CommandId.MOVE_PROCESS_STEP_UP:
            return move_step(recipe, action_id, command_id, -1)
        if command_id is CommandId.MOVE_PROCESS_STEP_DOWN:
            return move_step(recipe, action_id, command_id, 1)
        if command_id is CommandId.ENABLE_PROCESS_STEP:
            return set_step_enabled(recipe, action_id, command_id, True)
        if command_id is CommandId.DISABLE_PROCESS_STEP:
            return set_step_enabled(recipe, action_id, command_id, False)
        if command_id is CommandId.EDIT_PROCESS_STEP:
            return edit_step(recipe, action_id, command_id)
        if command_id in {CommandId.PREVIEW_RECIPE, CommandId.PREVIEW_RECIPE_THROUGH_STEP}:
            return preview_recipe(recipe, action_id, command_id)
        if command_id is CommandId.VALIDATE_RECIPE:
            return _validate(recipe, command_id)
        return RecipeEditorActionResult(
            "unavailable",
            command_id,
            f"{command_id.value} is not wired to a recipe workflow yet.",
            recipe,
            next_ui_hint="The action is known and should stay modeless until wired.",
        )


def _dispatch_material_action(
    recipe: ProcessRecipe | None,
    action_id: str,
    command_id: CommandId,
) -> RecipeEditorActionResult | None:
    if command_id is CommandId.ADD_MATERIAL:
        return add_material(recipe, command_id)
    if command_id is CommandId.DELETE_MATERIAL:
        return delete_material(recipe, action_id, command_id)
    if command_id is CommandId.DUPLICATE_MATERIAL:
        return duplicate_material(recipe, action_id, command_id)
    if command_id is CommandId.TOGGLE_MATERIAL_VISIBILITY:
        return toggle_material_visibility(recipe, action_id, command_id)
    if command_id is CommandId.FIND_MATERIAL_USAGE:
        return find_material_usage(recipe, action_id, command_id)
    if command_id is CommandId.EDIT_MATERIAL:
        return edit_material(recipe, action_id, command_id)
    return None


def _select_card(
    recipe: ProcessRecipe | None,
    card_id: str,
) -> RecipeEditorActionResult:
    if recipe is None:
        return RecipeEditorActionResult(
            "unavailable",
            message="Load or create a recipe before selecting cards.",
            next_ui_hint="Open or create a recipe first.",
        )
    updated = _with_metadata(recipe, selected_card_id=card_id)
    return RecipeEditorActionResult(
        "success",
        message=f"Selected {card_id}.",
        recipe=updated,
        selected_card_id=card_id,
        next_ui_hint="Recipe details are ready for inline editing.",
    )


def _add_step_template(
    recipe: ProcessRecipe | None,
    action_id: str,
    command_id: CommandId,
) -> RecipeEditorActionResult:
    if recipe is None:
        return RecipeEditorActionResult(
            "unavailable",
            command_id,
            "Create or open a recipe before adding process steps.",
            next_ui_hint="Use New Recipe or Open Recipe first.",
        )
    kind = _step_kind_from_action(action_id)
    if kind is None:
        return RecipeEditorActionResult(
            "error",
            command_id,
            f"Recipe step template is missing or invalid: {action_id}",
            recipe,
            next_ui_hint="Choose a supported process step template.",
        )
    step_id = _next_step_id(recipe, kind)
    step = ProcessStep(
        step_id,
        kind,
        parameters={"enabled": True, "template": True},
        notes=f"New {kind.value.replace('_', ' ')} step.",
    )
    updated = _with_metadata(
        replace(recipe, steps=(*recipe.steps, step)),
        dirty=True,
        selected_card_id=f"step:{step_id}",
    )
    return RecipeEditorActionResult(
        "success",
        command_id,
        f"Added {kind.value.replace('_', ' ')} step template.",
        updated,
        f"step:{step_id}",
        next_ui_hint="Fill required fields in the process step details panel.",
    )


def _validate(
    recipe: ProcessRecipe | None,
    command_id: CommandId,
) -> RecipeEditorActionResult:
    if recipe is None:
        return RecipeEditorActionResult(
            "unavailable",
            command_id,
            "No recipe is loaded for validation.",
            next_ui_hint="Open or create a recipe first.",
        )
    warnings = tuple(f"recipe-warning-{index}" for index, _ in enumerate(recipe.validate(), 1))
    status = "warning" if warnings else "success"
    message = f"Recipe validation found {len(warnings)} warning(s)."
    return RecipeEditorActionResult(status, command_id, message, recipe, warning_ids=warnings)


def _step_kind_from_action(action_id: str) -> ProcessStepKind | None:
    if ":" not in action_id:
        return None
    try:
        return ProcessStepKind(action_id.split(":", 1)[1])
    except ValueError:
        return None


def _next_step_id(recipe: ProcessRecipe, kind: ProcessStepKind) -> str:
    existing = {step.id for step in recipe.steps}
    base = kind.value.replace("_", "-")
    index = len(recipe.steps) + 1
    step_id = f"step-{index:03d}-{base}"
    while step_id in existing:
        index += 1
        step_id = f"step-{index:03d}-{base}"
    return step_id


def _with_metadata(recipe: ProcessRecipe, **updates: object) -> ProcessRecipe:
    metadata = dict(recipe.metadata or {})
    metadata.update(updates)
    return replace(recipe, metadata=metadata)
