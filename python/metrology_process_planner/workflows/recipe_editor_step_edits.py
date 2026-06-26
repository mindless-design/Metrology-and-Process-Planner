"""Process-step field-edit workflows for the modeless recipe editor."""

from __future__ import annotations

from dataclasses import replace

from metrology_process_planner.domains.commands import CommandId
from metrology_process_planner.domains.process import (
    MaskPolarity,
    ProcessRecipe,
    ProcessStep,
    ThicknessSpec,
)
from metrology_process_planner.domains.units import UnitParseError, parse_length
from metrology_process_planner.workflows.recipe_editor_results import RecipeEditorActionResult


def edit_step(
    recipe: ProcessRecipe | None,
    action_id: str,
    command_id: CommandId,
) -> RecipeEditorActionResult:
    """Apply one process-step detail edit without saving the recipe file."""

    if recipe is None:
        return RecipeEditorActionResult(
            "unavailable",
            command_id,
            "Open or create a recipe before editing process steps.",
            next_ui_hint="Use Open Recipe or New Recipe first.",
        )
    target = _edit_target(action_id)
    if target is None:
        return _bad_edit(recipe, command_id, "Process-step edit payload is incomplete.")
    step_id, field_key, value = target
    step = next((item for item in recipe.steps if item.id == step_id), None)
    if step is None:
        return _bad_edit(recipe, command_id, f"Process step '{step_id}' was not found.")
    edited = _apply_step_edit(recipe, step, field_key, value)
    if isinstance(edited, RecipeEditorActionResult):
        return edited
    return RecipeEditorActionResult(
        "success",
        command_id,
        f"Updated process step '{step_id}' {field_key}.",
        edited,
        f"step:{step_id}",
        next_ui_hint="Review the plain-language summary and validation messages.",
    )


def _edit_target(action_id: str) -> tuple[str, str, str] | None:
    parts = action_id.split(":", 3)
    if len(parts) != 4:
        return None
    _, step_id, field_key, value = parts
    if not step_id or not field_key:
        return None
    return step_id, field_key, value


def _apply_step_edit(
    recipe: ProcessRecipe,
    step: ProcessStep,
    field_key: str,
    value: str,
) -> ProcessRecipe | RecipeEditorActionResult:
    if field_key in {"name", "enabled"}:
        return _with_step(recipe, _with_parameter(step, field_key, value))
    if field_key == "material_id":
        return _with_step(recipe, replace(step, material_id=value.strip() or None))
    if field_key == "target_material_ids":
        return _with_step(recipe, replace(step, target_material_ids=_csv_tuple(value)))
    if field_key == "stop_material_ids":
        return _with_step(recipe, replace(step, stop_material_ids=_csv_tuple(value)))
    if field_key == "mask_polarity":
        return _with_mask_polarity(recipe, step, value)
    if field_key == "thickness":
        return _with_thickness(recipe, step, value)
    if field_key == "notes":
        return _with_step(recipe, replace(step, notes=value))
    return _bad_edit(
        recipe,
        CommandId.EDIT_PROCESS_STEP,
        f"Step field '{field_key}' is not editable.",
    )


def _with_parameter(step: ProcessStep, field_key: str, value: str) -> ProcessStep:
    parameters = dict(step.parameters or {})
    parameters[field_key] = _truthy(value) if field_key == "enabled" else value.strip()
    return replace(step, parameters=parameters)


def _with_mask_polarity(
    recipe: ProcessRecipe,
    step: ProcessStep,
    value: str,
) -> ProcessRecipe | RecipeEditorActionResult:
    try:
        polarity = MaskPolarity(value.strip())
    except ValueError:
        return _bad_edit(
            recipe,
            CommandId.EDIT_PROCESS_STEP,
            "Mask polarity must be direct or inverted.",
        )
    return _with_step(recipe, replace(step, mask_polarity=polarity))


def _with_thickness(
    recipe: ProcessRecipe,
    step: ProcessStep,
    value: str,
) -> ProcessRecipe | RecipeEditorActionResult:
    try:
        parsed = parse_length(value, default_unit="um", allow_plain_angstrom=True)
    except UnitParseError as error:
        return _bad_edit(
            recipe,
            CommandId.EDIT_PROCESS_STEP,
            f"Thickness must be a numeric length. {error}",
        )
    current = step.thickness
    display_unit = parsed.display_unit or (current.display_unit if current is not None else "um")
    thickness = ThicknessSpec(parsed.value_um, unit="um", display_unit=display_unit)
    return _with_step(recipe, replace(step, thickness=thickness))


def _with_step(recipe: ProcessRecipe, replacement: ProcessStep) -> ProcessRecipe:
    metadata = dict(recipe.metadata or {})
    metadata.update({"dirty": True, "selected_card_id": f"step:{replacement.id}"})
    return replace(
        recipe,
        steps=tuple(replacement if item.id == replacement.id else item for item in recipe.steps),
        metadata=metadata,
    )


def _csv_tuple(value: str) -> tuple[str, ...]:
    return tuple(item.strip() for item in value.split(",") if item.strip())


def _truthy(value: str) -> bool:
    return value.strip().lower() in {"1", "true", "yes", "y", "on", "enabled"}


def _bad_edit(
    recipe: ProcessRecipe,
    command_id: CommandId,
    message: str,
) -> RecipeEditorActionResult:
    return RecipeEditorActionResult(
        "error",
        command_id,
        message,
        recipe,
        next_ui_hint="Select a process-step field and retry the edit.",
    )
