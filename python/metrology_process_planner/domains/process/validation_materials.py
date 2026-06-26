"""Material-level structured process recipe validation."""

from __future__ import annotations

from metrology_process_planner.domains.process.materials import Material
from metrology_process_planner.domains.process.steps import ProcessStep
from metrology_process_planner.domains.process.validation_messages import (
    RecipeValidationMessage,
    recipe_validation_message,
)


def material_messages(materials: tuple[Material, ...]) -> tuple[RecipeValidationMessage, ...]:
    """Return structured validation messages for recipe materials."""

    messages: list[RecipeValidationMessage] = []
    seen: set[str] = set()
    for material in materials:
        messages.extend(_single_material_messages(material, seen))
        seen.add(material.id)
    if not materials:
        messages.append(
            recipe_validation_message(
                "recipe-materials-empty",
                "blocking",
                "recipe",
                "Recipe must define at least one material.",
                repair="Add a material card.",
            )
        )
    return tuple(messages)


def unused_material_messages(
    materials: tuple[Material, ...],
    steps: tuple[ProcessStep, ...],
) -> tuple[RecipeValidationMessage, ...]:
    """Return informational messages for material records not referenced by steps."""

    used = {step.material_id for step in steps if step.material_id}
    for step in steps:
        used.update(step.target_material_ids)
        used.update(step.stop_material_ids)
    return tuple(
        recipe_validation_message(
            f"material-unused-{material.id}",
            "info",
            "material",
            f"Material {material.id} is not used by any enabled process step.",
            material_id=material.id,
            repair="Use it in a step or remove it.",
        )
        for material in materials
        if material.id not in used
    )


def _single_material_messages(
    material: Material,
    seen: set[str],
) -> tuple[RecipeValidationMessage, ...]:
    messages: list[RecipeValidationMessage] = []
    messages.extend(_material_identity_messages(material, seen))
    if not material.name:
        messages.append(
            recipe_validation_message(
                f"material-name-{material.id}",
                "error",
                "material",
                f"Material {material.id or '<missing>'} is missing a name.",
                material_id=material.id,
                repair="Add a material name.",
            )
        )
    if not material.color:
        messages.append(
            recipe_validation_message(
                f"material-color-{material.id}",
                "warning",
                "material",
                f"Material {material.id or '<missing>'} is missing a display color.",
                material_id=material.id,
                repair="Choose a display color.",
            )
        )
    return tuple(messages)


def _material_identity_messages(
    material: Material,
    seen: set[str],
) -> tuple[RecipeValidationMessage, ...]:
    if not material.id:
        return (
            recipe_validation_message(
                "material-missing-id",
                "blocking",
                "material",
                "Material is missing an ID.",
                material_id=material.id,
                repair="Assign a stable material ID.",
            ),
        )
    if material.id in seen:
        return (
            recipe_validation_message(
                f"material-duplicate-{material.id}",
                "blocking",
                "material",
                f"Duplicate material ID: {material.id}.",
                material_id=material.id,
                repair="Rename one material to a unique ID.",
            ),
        )
    return ()
