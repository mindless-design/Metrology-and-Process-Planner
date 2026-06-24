"""Material field-edit workflows for the modeless recipe editor."""

from __future__ import annotations

from dataclasses import replace

from metrology_process_planner.app.command_types import CommandId
from metrology_process_planner.domains.process import Material, ProcessRecipe
from metrology_process_planner.workflows.recipe_editor_material_helpers import replace_material
from metrology_process_planner.workflows.recipe_editor_results import RecipeEditorActionResult

_MATERIAL_METADATA_FIELDS = {"category": "material_categories", "notes": "material_notes"}


def edit_material(
    recipe: ProcessRecipe | None,
    action_id: str,
    command_id: CommandId,
) -> RecipeEditorActionResult:
    """Apply one material detail-field edit without saving the recipe file."""

    if recipe is None:
        return RecipeEditorActionResult(
            "unavailable",
            command_id,
            "Open or create a recipe before editing materials.",
            next_ui_hint="Use Open Recipe or New Recipe first.",
        )
    target = _edit_target(action_id)
    if target is None:
        return _bad_edit(recipe, command_id, "Material edit payload is incomplete.")
    material_id, field_key, value = target
    material = next((item for item in recipe.materials if item.id == material_id), None)
    if material is None:
        return _bad_edit(recipe, command_id, f"Material '{material_id}' was not found.")
    edited = _apply_material_edit(recipe, material, field_key, value)
    if isinstance(edited, RecipeEditorActionResult):
        return edited
    return RecipeEditorActionResult(
        "success",
        command_id,
        f"Updated material '{material_id}' {field_key}.",
        edited,
        f"material:{material_id}",
        next_ui_hint="Review validation messages, then save the recipe when ready.",
    )


def _edit_target(action_id: str) -> tuple[str, str, str] | None:
    parts = action_id.split(":", 3)
    if len(parts) != 4:
        return None
    _, material_id, field_key, value = parts
    if not material_id or not field_key:
        return None
    return material_id, field_key, value


def _apply_material_edit(
    recipe: ProcessRecipe,
    material: Material,
    field_key: str,
    value: str,
) -> ProcessRecipe | RecipeEditorActionResult:
    if field_key == "name":
        return _with_material(recipe, replace(material, name=value.strip() or material.id))
    if field_key == "color":
        return _with_material(recipe, replace(material, color=value.strip() or "#888888"))
    if field_key == "visible":
        return _with_material(recipe, replace(material, visible=_truthy(value)))
    if field_key in _MATERIAL_METADATA_FIELDS:
        return _with_material_metadata(recipe, material.id, field_key, value)
    return _bad_edit(
        recipe,
        CommandId.EDIT_MATERIAL,
        f"Material field '{field_key}' is not editable.",
    )


def _with_material(recipe: ProcessRecipe, material: Material) -> ProcessRecipe:
    return _with_metadata(
        replace_material(recipe, material),
        dirty=True,
        selected_card_id=f"material:{material.id}",
    )


def _with_material_metadata(
    recipe: ProcessRecipe,
    material_id: str,
    field_key: str,
    value: str,
) -> ProcessRecipe:
    metadata = dict(recipe.metadata or {})
    bucket_key = _MATERIAL_METADATA_FIELDS[field_key]
    bucket = dict(metadata.get(bucket_key, {}))
    bucket[material_id] = value.strip()
    metadata[bucket_key] = bucket
    metadata["dirty"] = True
    metadata["selected_card_id"] = f"material:{material_id}"
    return replace(recipe, metadata=metadata)


def _with_metadata(recipe: ProcessRecipe, **updates: object) -> ProcessRecipe:
    metadata = dict(recipe.metadata or {})
    metadata.update(updates)
    return replace(recipe, metadata=metadata)


def _truthy(value: str) -> bool:
    return value.strip().lower() in {"1", "true", "yes", "y", "on", "visible"}


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
        next_ui_hint="Select a material field and retry the edit.",
    )
