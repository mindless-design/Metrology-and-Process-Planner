"""Build card-based recipe editor view models."""

from __future__ import annotations

from collections import Counter

from metrology_process_planner.domains.process import (
    Material,
    ProcessRecipe,
    ProcessStep,
    ProcessStepKind,
)
from metrology_process_planner.domains.process.validation import validate_step
from metrology_process_planner.ui.recipe_editor.card_actions import process_step_card_actions
from metrology_process_planner.ui.recipe_editor.summaries import (
    layer_label,
    material_label,
    material_labels,
    operation_label,
    step_enabled,
    step_name,
    step_summary,
    thickness_summary,
)
from metrology_process_planner.ui.recipe_editor.view_models import (
    RecipeLayerCardViewModel,
    RecipeMaterialCardViewModel,
    RecipePreviewViewModel,
    RecipeStepCardViewModel,
    RecipeSummaryViewModel,
)
from metrology_process_planner.ui.shell.view_models import EditorActionViewModel


def material_cards(recipe: ProcessRecipe) -> tuple[RecipeMaterialCardViewModel, ...]:
    """Return editable material cards with usage and warning badges."""

    usage = _material_usage(recipe.steps)
    metadata = dict(recipe.metadata or {})
    selected = str(metadata.get("selected_card_id", ""))
    return tuple(
        RecipeMaterialCardViewModel(
            material.id,
            material.name,
            _material_category(recipe, material),
            material.color,
            material.visible,
            usage[material.id],
            _material_warning_count(material, usage[material.id]),
            selected == f"material:{material.id}",
            bool(metadata.get("dirty", False)),
        )
        for material in recipe.materials
    )


def step_cards(recipe: ProcessRecipe) -> tuple[RecipeStepCardViewModel, ...]:
    """Return ordered process-step cards with plain-language summaries."""

    labels = material_labels(recipe)
    material_ids = set(labels)
    metadata = dict(recipe.metadata or {})
    selected = str(metadata.get("selected_card_id", ""))
    return tuple(
        RecipeStepCardViewModel(
            step.id,
            index,
            step_name(step),
            operation_label(step.kind),
            step_enabled(step),
            material_label(step, labels),
            layer_label(step),
            thickness_summary(step),
            _status_label(step),
            step_summary(step, labels),
            len(validate_step(step, material_ids)),
            selected == f"step:{step.id}",
            bool(metadata.get("dirty", False)),
            process_step_card_actions(step.id, step_enabled(step)),
        )
        for index, step in enumerate(recipe.steps, start=1)
    )


def layer_cards(recipe: ProcessRecipe) -> tuple[RecipeLayerCardViewModel, ...]:
    """Return unique layer/mask cards used by process steps."""

    by_key: dict[tuple[str, int, int], list[str]] = {}
    labels: dict[tuple[str, int, int], str] = {}
    for step in recipe.steps:
        if step.layer is None:
            continue
        key = (step.layer.source, step.layer.layer, step.layer.datatype)
        by_key.setdefault(key, []).append(step.id)
        labels[key] = step.layer.name or f"{step.layer.layer}/{step.layer.datatype}"
    return tuple(
        RecipeLayerCardViewModel(
            f"layer:{source}:{layer}:{datatype}",
            labels[(source, layer, datatype)],
            source,
            layer,
            datatype,
            tuple(step_ids),
        )
        for (source, layer, datatype), step_ids in sorted(by_key.items())
    )


def summary_model(recipe: ProcessRecipe) -> RecipeSummaryViewModel:
    """Return the plain-language recipe summary tab model."""

    usage = _material_usage(recipe.steps)
    disabled = tuple(step.id for step in recipe.steps if not step_enabled(step))
    return RecipeSummaryViewModel(
        tuple(
            f"{index}. {step_summary(step, material_labels(recipe))}"
            for index, step in enumerate(recipe.steps, start=1)
        ),
        len(recipe.materials),
        len(recipe.steps),
        tuple(material.id for material in recipe.materials if usage[material.id] == 0),
        disabled,
    )


def preview_model(recipe: ProcessRecipe) -> RecipePreviewViewModel:
    """Return a non-blocking placeholder until live preview is wired."""

    selected = str(dict(recipe.metadata or {}).get("selected_step_id", ""))
    return RecipePreviewViewModel(
        "unavailable",
        "Recipe preview backend is not connected yet.",
        selected,
    )


def material_actions() -> tuple[EditorActionViewModel, ...]:
    """Return command-shaped material tab actions."""

    return (EditorActionViewModel("AddMaterial", "Add Material"),)


def step_templates() -> tuple[EditorActionViewModel, ...]:
    """Return add-step template commands for supported process operations."""

    return tuple(
        EditorActionViewModel(f"AddProcessStep:{kind.value}", operation_label(kind))
        for kind in ProcessStepKind
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


def _material_category(recipe: ProcessRecipe, material: Material) -> str:
    categories = dict(recipe.metadata or {}).get("material_categories", {})
    if isinstance(categories, dict) and material.id in categories:
        return str(categories[material.id])
    return "other"


def _material_warning_count(material: Material, usage_count: int) -> int:
    checks = (not material.name, not material.color, usage_count == 0)
    return sum(1 for failed in checks if failed)


def _status_label(step: ProcessStep) -> str:
    return "Enabled" if step_enabled(step) else "Disabled"
