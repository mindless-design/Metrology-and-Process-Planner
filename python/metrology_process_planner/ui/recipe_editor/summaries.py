"""Plain-language process recipe summaries."""

from __future__ import annotations

from metrology_process_planner.domains.process import ProcessRecipe, ProcessStep, ProcessStepKind
from metrology_process_planner.domains.session.display_units import (
    DisplayUnitPreferences,
    format_length,
)


def material_labels(recipe: ProcessRecipe) -> dict[str, str]:
    """Return material id to display-name mapping."""

    return {material.id: material.name for material in recipe.materials}


def step_name(step: ProcessStep) -> str:
    """Return a display name for one process step."""

    if step.name:
        return step.name
    name = step.parameters.get("name") if step.parameters is not None else None
    return str(name) if name else operation_label(step.kind)


def operation_label(kind: ProcessStepKind) -> str:
    """Return a user-facing operation label."""

    labels = {
        ProcessStepKind.SUBSTRATE: "Initialize substrate / wafer",
        ProcessStepKind.BLANKET_DEPOSITION: "Blanket deposition",
        ProcessStepKind.PATTERNED_DEPOSITION: "Patterned deposition",
        ProcessStepKind.CONFORMAL_COATING: "Conformal coating",
        ProcessStepKind.CONFORMAL_DEPOSITION: "Conformal coating",
        ProcessStepKind.DIRECTIONAL_ETCH: "Directional etch",
        ProcessStepKind.ISOTROPIC_ETCH: "Isotropic etch",
        ProcessStepKind.TAPERED_ETCH: "Tapered etch",
        ProcessStepKind.PLANARIZATION: "Planarization",
        ProcessStepKind.CMP_PLANARIZATION: "CMP",
        ProcessStepKind.ANNOTATION_ONLY: "Annotation-only step",
    }
    return labels[kind]


def step_enabled(step: ProcessStep) -> bool:
    """Return whether a process step is enabled."""

    return bool((step.parameters or {}).get("enabled", step.enabled))


def material_label(step: ProcessStep, labels: dict[str, str]) -> str:
    """Return the display material for a step."""

    if step.material_id is None:
        return ""
    return labels.get(step.material_id, step.material_id)


def layer_label(step: ProcessStep) -> str:
    """Return the display layer/mask label for a step."""

    if step.layer is None:
        return ""
    return step.layer.name or f"{step.layer.layer}/{step.layer.datatype}"


def thickness_summary(
    step: ProcessStep,
    preferences: DisplayUnitPreferences | None = None,
) -> str:
    """Return a compact thickness/depth/plane summary."""

    display_preference = (
        preferences.film_thickness if preferences is not None else "auto"
    )
    if step.thickness is not None:
        display_unit = (
            display_preference
            if display_preference != "auto"
            else step.thickness.display_unit or step.thickness.unit
        )
        return f"{format_length(step.thickness.target, step.thickness.unit, display_unit)} target"
    if (
        step.planarization_profile is not None
        and step.planarization_profile.target_height is not None
    ):
        value = format_length(
            step.planarization_profile.target_height,
            "um",
            display_preference,
        )
        return f"target plane {value}"
    return ""


def step_summary(step: ProcessStep, labels: dict[str, str]) -> str:
    """Return a plain-language summary for a process step."""

    return _SUMMARY_BUILDERS[step.kind](step, labels)


def target_materials(step: ProcessStep) -> str:
    """Return target material display text."""

    return ", ".join(step.target_material_ids) if step.target_material_ids else "target materials"


def _substrate_summary(step: ProcessStep, labels: dict[str, str]) -> str:
    return f"Start with {_material(step, labels)} substrate."


def _blanket_summary(step: ProcessStep, labels: dict[str, str]) -> str:
    return f"Deposit {thickness_summary(step) or _material(step, labels)} everywhere."


def _patterned_summary(step: ProcessStep, labels: dict[str, str]) -> str:
    layer = layer_label(step) or "selected mask"
    return f"Deposit {thickness_summary(step) or _material(step, labels)} where {layer} is active."


def _conformal_summary(step: ProcessStep, labels: dict[str, str]) -> str:
    return f"Conformally coat exposed surfaces with {_material(step, labels)}."


def _directional_etch_summary(step: ProcessStep, labels: dict[str, str]) -> str:
    del labels
    return f"Directionally etch exposed {target_materials(step)}."


def _isotropic_etch_summary(step: ProcessStep, labels: dict[str, str]) -> str:
    del labels
    return f"Isotropically etch exposed {target_materials(step)}."


def _tapered_etch_summary(step: ProcessStep, labels: dict[str, str]) -> str:
    del labels
    return f"Taper etch exposed {target_materials(step)}."


def _planarization_summary(step: ProcessStep, labels: dict[str, str]) -> str:
    del labels
    return f"Planarize to {thickness_summary(step) or 'the target plane'}."


def _cmp_summary(step: ProcessStep, labels: dict[str, str]) -> str:
    del labels
    return f"CMP planarize to {thickness_summary(step) or 'the stop condition'}."


def _annotation_summary(step: ProcessStep, labels: dict[str, str]) -> str:
    del labels
    return step.notes or "Annotation-only process note."


def _material(step: ProcessStep, labels: dict[str, str]) -> str:
    return material_label(step, labels) or "selected material"


_SUMMARY_BUILDERS = {
    ProcessStepKind.SUBSTRATE: _substrate_summary,
    ProcessStepKind.BLANKET_DEPOSITION: _blanket_summary,
    ProcessStepKind.PATTERNED_DEPOSITION: _patterned_summary,
    ProcessStepKind.CONFORMAL_COATING: _conformal_summary,
    ProcessStepKind.CONFORMAL_DEPOSITION: _conformal_summary,
    ProcessStepKind.DIRECTIONAL_ETCH: _directional_etch_summary,
    ProcessStepKind.ISOTROPIC_ETCH: _isotropic_etch_summary,
    ProcessStepKind.TAPERED_ETCH: _tapered_etch_summary,
    ProcessStepKind.PLANARIZATION: _planarization_summary,
    ProcessStepKind.CMP_PLANARIZATION: _cmp_summary,
    ProcessStepKind.ANNOTATION_ONLY: _annotation_summary,
}
