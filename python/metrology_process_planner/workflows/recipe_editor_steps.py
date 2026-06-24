"""Process-step action handlers for modeless recipe editing."""

from __future__ import annotations

from dataclasses import replace

from metrology_process_planner.app.command_types import CommandId
from metrology_process_planner.domains.process import ProcessRecipe, ProcessStep
from metrology_process_planner.workflows.recipe_editor_results import RecipeEditorActionResult


def duplicate_step(
    recipe: ProcessRecipe | None,
    action_id: str,
    command_id: CommandId,
) -> RecipeEditorActionResult:
    """Duplicate one process step and select the copy."""

    found = _find_step(recipe, action_id, command_id)
    if isinstance(found, RecipeEditorActionResult):
        return found
    current_recipe, step, index = found
    duplicate_id = _copy_step_id(current_recipe, step.id)
    duplicate = replace(step, id=duplicate_id)
    steps = current_recipe.steps[: index + 1] + (duplicate,) + current_recipe.steps[index + 1 :]
    updated = _with_metadata(current_recipe, steps, selected_card_id=f"step:{duplicate_id}")
    return RecipeEditorActionResult(
        "success",
        command_id,
        f"Duplicated step '{step.id}'.",
        updated,
        f"step:{duplicate_id}",
        next_ui_hint="Review the duplicated step fields before saving.",
    )


def delete_step(
    recipe: ProcessRecipe | None,
    action_id: str,
    command_id: CommandId,
) -> RecipeEditorActionResult:
    """Delete one process step from the in-memory recipe."""

    found = _find_step(recipe, action_id, command_id)
    if isinstance(found, RecipeEditorActionResult):
        return found
    current_recipe, step, _index = found
    steps = tuple(item for item in current_recipe.steps if item.id != step.id)
    updated = _with_metadata(current_recipe, steps, selected_card_id="")
    return RecipeEditorActionResult(
        "success",
        command_id,
        f"Deleted step '{step.id}'.",
        updated,
        next_ui_hint="Review the process flow before saving.",
    )


def move_step(
    recipe: ProcessRecipe | None,
    action_id: str,
    command_id: CommandId,
    direction: int,
) -> RecipeEditorActionResult:
    """Move one process step up or down in the ordered flow."""

    found = _find_step(recipe, action_id, command_id)
    if isinstance(found, RecipeEditorActionResult):
        return found
    current_recipe, step, index = found
    target = index + direction
    if target < 0 or target >= len(current_recipe.steps):
        return RecipeEditorActionResult(
            "blocked",
            command_id,
            f"Step '{step.id}' cannot move further in that direction.",
            current_recipe,
            f"step:{step.id}",
            next_ui_hint="Choose another step or direction.",
        )
    steps = list(current_recipe.steps)
    steps[index], steps[target] = steps[target], steps[index]
    updated = _with_metadata(current_recipe, tuple(steps), selected_card_id=f"step:{step.id}")
    return RecipeEditorActionResult(
        "success",
        command_id,
        f"Moved step '{step.id}'.",
        updated,
        f"step:{step.id}",
        next_ui_hint="Review the reordered process flow before saving.",
    )


def set_step_enabled(
    recipe: ProcessRecipe | None,
    action_id: str,
    command_id: CommandId,
    enabled: bool,
) -> RecipeEditorActionResult:
    """Enable or disable one process step."""

    found = _find_step(recipe, action_id, command_id)
    if isinstance(found, RecipeEditorActionResult):
        return found
    current_recipe, step, _index = found
    parameters = dict(step.parameters or {})
    parameters["enabled"] = enabled
    updated_step = replace(step, parameters=parameters)
    steps = tuple(updated_step if item.id == step.id else item for item in current_recipe.steps)
    updated = _with_metadata(current_recipe, steps, selected_card_id=f"step:{step.id}")
    state = "enabled" if enabled else "disabled"
    return RecipeEditorActionResult(
        "success",
        command_id,
        f"Step '{step.id}' {state}.",
        updated,
        f"step:{step.id}",
        next_ui_hint="Review validation messages before saving.",
    )


def _find_step(
    recipe: ProcessRecipe | None,
    action_id: str,
    command_id: CommandId,
) -> tuple[ProcessRecipe, ProcessStep, int] | RecipeEditorActionResult:
    if recipe is None:
        return RecipeEditorActionResult(
            "unavailable",
            command_id,
            "Open or create a recipe before editing process steps.",
            next_ui_hint="Use Open Recipe or New Recipe first.",
        )
    step_id = _step_id_from_action(recipe, action_id)
    for index, step in enumerate(recipe.steps):
        if step.id == step_id:
            return recipe, step, index
    return RecipeEditorActionResult(
        "error",
        command_id,
        "Choose a process step card before running this action.",
        recipe,
        next_ui_hint="Select a process step and retry.",
    )


def _step_id_from_action(recipe: ProcessRecipe, action_id: str) -> str:
    if ":" in action_id:
        return action_id.split(":", 1)[1]
    selected = str(dict(recipe.metadata or {}).get("selected_card_id", ""))
    if selected.startswith("step:"):
        return selected.removeprefix("step:")
    return ""


def _copy_step_id(recipe: ProcessRecipe, step_id: str) -> str:
    existing = {step.id for step in recipe.steps}
    base = f"{step_id}-copy"
    candidate = base
    index = 2
    while candidate in existing:
        candidate = f"{base}-{index}"
        index += 1
    return candidate


def _with_metadata(
    recipe: ProcessRecipe,
    steps: tuple[ProcessStep, ...],
    **updates: object,
) -> ProcessRecipe:
    metadata = dict(recipe.metadata or {})
    metadata.update({"dirty": True, **updates})
    return replace(recipe, steps=steps, metadata=metadata)
