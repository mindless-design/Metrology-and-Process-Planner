"""Selected-card detail panel models for the recipe editor."""

from __future__ import annotations

from metrology_process_planner.domains.process import (
    Material,
    ProcessRecipe,
    ProcessStep,
)
from metrology_process_planner.ui.recipe_editor.card_actions import (
    material_card_actions,
    process_step_card_actions,
)
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
from metrology_process_planner.ui.recipe_editor.view_models import RecipeDetailPanelViewModel
from metrology_process_planner.ui.shell.view_models import (
    EditorActionViewModel,
    MetadataFieldViewModel,
)


def selected_detail(recipe: ProcessRecipe) -> RecipeDetailPanelViewModel | None:
    """Return editable details for the selected recipe card."""

    selected = str(dict(recipe.metadata or {}).get("selected_card_id", ""))
    if selected.startswith("material:"):
        return _material_detail(recipe, selected.removeprefix("material:"))
    if selected.startswith("step:"):
        return _step_detail(recipe, selected.removeprefix("step:"))
    if selected.startswith("layer:"):
        return _layer_detail(recipe, selected)
    return None


def _material_detail(
    recipe: ProcessRecipe,
    material_id: str,
) -> RecipeDetailPanelViewModel | None:
    material = _material_by_id(recipe, material_id)
    if material is None:
        return None
    category = _material_category(recipe, material)
    return RecipeDetailPanelViewModel(
        f"material:{material.id}",
        "material",
        material.name,
        (
            MetadataFieldViewModel("name", "Material Name", material.name, required=True),
            MetadataFieldViewModel("id", "Material ID", material.id, read_only=True),
            MetadataFieldViewModel("category", "Category", category),
            MetadataFieldViewModel("color", "Display Color", material.color, required=True),
            MetadataFieldViewModel("visible", "Visible", _bool_text(material.visible)),
            MetadataFieldViewModel("notes", "Notes", _material_notes(recipe, material.id)),
        ),
        material_card_actions(material.id),
        summary=f"{material.name} is a {category} material.",
    )


def _step_detail(recipe: ProcessRecipe, step_id: str) -> RecipeDetailPanelViewModel | None:
    step = _step_by_id(recipe, step_id)
    if step is None:
        return None
    labels = material_labels(recipe)
    return RecipeDetailPanelViewModel(
        f"step:{step.id}",
        "step",
        step_name(step),
        _step_fields(step, labels),
        process_step_card_actions(step.id, step_enabled(step)),
        summary=step_summary(step, labels),
    )


def _layer_detail(recipe: ProcessRecipe, card_id: str) -> RecipeDetailPanelViewModel | None:
    for step in recipe.steps:
        if step.layer is None:
            continue
        if card_id == f"layer:{step.layer.source}:{step.layer.layer}:{step.layer.datatype}":
            layer = step.layer
            return RecipeDetailPanelViewModel(
                card_id,
                "layer",
                layer_label(step),
                (
                    MetadataFieldViewModel("name", "Layer Name", layer.name),
                    MetadataFieldViewModel("source", "Source", layer.source),
                    MetadataFieldViewModel("layer", "Layer", str(layer.layer)),
                    MetadataFieldViewModel("datatype", "Datatype", str(layer.datatype)),
                ),
                (EditorActionViewModel("SelectLayerReference", "Select Layer Reference"),),
                summary=f"Used by layer/mask step references in {recipe.name}.",
            )
    return None


def _step_fields(
    step: ProcessStep,
    labels: dict[str, str],
) -> tuple[MetadataFieldViewModel, ...]:
    return (
        MetadataFieldViewModel("name", "Step Name", step_name(step), required=True),
        MetadataFieldViewModel("enabled", "Enabled", _bool_text(step_enabled(step))),
        MetadataFieldViewModel(
            "kind",
            "Operation Type",
            operation_label(step.kind),
            read_only=True,
        ),
        MetadataFieldViewModel("material_id", "Material", material_label(step, labels)),
        MetadataFieldViewModel(
            "target_material_ids",
            "Target Materials",
            _join(step.target_material_ids),
        ),
        MetadataFieldViewModel(
            "stop_material_ids",
            "Stop Materials",
            _join(step.stop_material_ids),
        ),
        MetadataFieldViewModel("layer", "Layer / Mask", layer_label(step)),
        MetadataFieldViewModel("mask_polarity", "Mask Polarity", step.mask_polarity.value),
        MetadataFieldViewModel("thickness", "Thickness / Depth / Plane", thickness_summary(step)),
        MetadataFieldViewModel("notes", "Notes", step.notes),
    )


def _material_by_id(recipe: ProcessRecipe, material_id: str) -> Material | None:
    return next((material for material in recipe.materials if material.id == material_id), None)


def _step_by_id(recipe: ProcessRecipe, step_id: str) -> ProcessStep | None:
    return next((step for step in recipe.steps if step.id == step_id), None)


def _material_category(recipe: ProcessRecipe, material: Material) -> str:
    categories = dict(recipe.metadata or {}).get("material_categories", {})
    if isinstance(categories, dict):
        return str(categories.get(material.id, "other"))
    return "other"


def _material_notes(recipe: ProcessRecipe, material_id: str) -> str:
    notes = dict(recipe.metadata or {}).get("material_notes", {})
    if isinstance(notes, dict):
        return str(notes.get(material_id, ""))
    return ""


def _bool_text(value: bool) -> str:
    return "yes" if value else "no"


def _join(values: tuple[str, ...]) -> str:
    return ", ".join(values)
