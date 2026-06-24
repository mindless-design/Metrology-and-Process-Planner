"""Inline recipe validation view-model mapping."""

from __future__ import annotations

from collections import Counter

from metrology_process_planner.domains.process import Material, ProcessRecipe, ProcessStep
from metrology_process_planner.ui.recipe_editor.view_models import (
    RecipeValidationMessageViewModel,
)


def validation_messages(recipe: ProcessRecipe) -> tuple[RecipeValidationMessageViewModel, ...]:
    """Return inline validation rows linked to recipe cards when possible."""

    messages = list(recipe.validate())
    messages.extend(_material_validation_messages(recipe))
    return tuple(
        RecipeValidationMessageViewModel(
            f"recipe-validation-{index}",
            "warning",
            _validation_source(message),
            message,
            related_card_id,
            _repair_suggestion(message),
            _select_action(related_card_id),
        )
        for index, message in enumerate(messages, start=1)
        for related_card_id in (_related_card_id(message, recipe),)
    )


def _material_validation_messages(recipe: ProcessRecipe) -> tuple[str, ...]:
    usage = _material_usage(recipe.steps)
    return tuple(
        message
        for material in recipe.materials
        for message in _material_messages(material, usage[material.id])
    )


def _material_usage(steps: tuple[ProcessStep, ...]) -> Counter[str]:
    usage: Counter[str] = Counter()
    for step in steps:
        for material_id in _step_material_ids(step):
            usage[material_id] += 1
    return usage


def _step_material_ids(step: ProcessStep) -> tuple[str, ...]:
    values = [step.material_id, *step.target_material_ids, *step.stop_material_ids]
    return tuple(value for value in values if value)


def _material_messages(material: Material, usage_count: int) -> tuple[str, ...]:
    checks = (
        (not material.name, f"Material {material.id} is missing a name."),
        (not material.color, f"Material {material.id} is missing a color."),
        (usage_count == 0, f"Material {material.id} is unused."),
    )
    return tuple(message for failed, message in checks if failed)


def _validation_source(message: str) -> str:
    if message.startswith("Material "):
        return "material"
    if message.startswith("Step "):
        return "step"
    if message.startswith("Window "):
        return "process_window"
    return "recipe"


def _related_card_id(message: str, recipe: ProcessRecipe) -> str:
    tokens = message.split()
    if len(tokens) < 2:
        return ""
    if tokens[0] == "Material":
        return f"material:{tokens[1]}"
    if tokens[0] == "Step":
        return _step_related_card(message, tokens[1].rstrip(":"), recipe)
    return ""


def _step_related_card(message: str, step_id: str, recipe: ProcessRecipe) -> str:
    if "layer reference" in message:
        return _first_matching_layer_card(recipe, step_id)
    return f"step:{step_id}"


def _first_matching_layer_card(recipe: ProcessRecipe, step_id: str) -> str:
    for step in recipe.steps:
        if step.id == step_id and step.layer is not None:
            return f"layer:{step.layer.source}:{step.layer.layer}:{step.layer.datatype}"
    return f"step:{step_id}"


def _repair_suggestion(message: str) -> str:
    if "unused" in message:
        return "Remove the material or assign it to a process step."
    if "missing a color" in message:
        return "Choose a display color for the material card."
    if "requires a layer reference" in message:
        return "Select or create a layer reference in the Layers / Masks tab."
    if "requires a material" in message:
        return "Assign a material in the step detail panel."
    if "requires a thickness" in message:
        return "Enter a target thickness or process window."
    return "Review the related card and fix the highlighted field."


def _select_action(related_card_id: str) -> str:
    if not related_card_id:
        return ""
    return f"SelectRecipeCard:{related_card_id}"
