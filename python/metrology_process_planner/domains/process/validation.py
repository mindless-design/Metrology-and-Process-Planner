"""Validation helpers for process recipes."""

from __future__ import annotations

from metrology_process_planner.domains.process.materials import Material
from metrology_process_planner.domains.process.steps import (
    ProcessStep,
    ProcessStepKind,
    ProcessWindow,
)

_DEPOSITION_KINDS = {
    ProcessStepKind.BLANKET_DEPOSITION,
    ProcessStepKind.PATTERNED_DEPOSITION,
    ProcessStepKind.CONFORMAL_COATING,
}


def validate_recipe(
    materials: tuple[Material, ...],
    steps: tuple[ProcessStep, ...],
    windows: tuple[ProcessWindow, ...],
) -> tuple[str, ...]:
    """Return warnings for an ordered process recipe."""

    material_ids = {material.id for material in materials}
    warnings = [*validate_recipe_shape(materials, steps)]
    for step in steps:
        warnings.extend(validate_step(step, material_ids))
    for window in windows:
        warnings.extend(f"Window {window.name}: {message}" for message in window.validate())
    return tuple(warnings)


def validate_recipe_shape(
    materials: tuple[Material, ...],
    steps: tuple[ProcessStep, ...],
) -> tuple[str, ...]:
    """Return warnings for missing top-level recipe parts."""

    checks = (
        (not materials, "Recipe must define at least one material."),
        (not steps, "Recipe must define at least one process step."),
    )
    return tuple(message for failed, message in checks if failed)


def validate_step(step: ProcessStep, material_ids: set[str]) -> tuple[str, ...]:
    """Return warnings for one process step."""

    warnings = [*validate_material_references(step, material_ids)]
    warnings.extend(validate_step_thickness(step))
    warnings.extend(validate_deposition_step(step))
    warnings.extend(validate_patterned_step(step))
    return tuple(warnings)


def validate_material_references(step: ProcessStep, material_ids: set[str]) -> tuple[str, ...]:
    """Return warnings for missing material references."""

    warnings: list[str] = []
    if step.material_id is not None and step.material_id not in material_ids:
        warnings.append(f"Step {step.id} references unknown material {step.material_id}.")
    for target_id in step.target_material_ids:
        if target_id not in material_ids:
            warnings.append(f"Step {step.id} targets unknown material {target_id}.")
    return tuple(warnings)


def validate_step_thickness(step: ProcessStep) -> tuple[str, ...]:
    """Return warnings for a step thickness specification."""

    if step.thickness is None:
        return ()
    return tuple(f"Step {step.id}: {message}" for message in step.thickness.validate())


def validate_deposition_step(step: ProcessStep) -> tuple[str, ...]:
    """Return warnings for deposition-specific requirements."""

    if step.kind not in _DEPOSITION_KINDS:
        return ()
    checks = (
        (step.material_id is None, f"Step {step.id} requires a material."),
        (step.thickness is None, f"Step {step.id} requires a thickness."),
    )
    return tuple(message for failed, message in checks if failed)


def validate_patterned_step(step: ProcessStep) -> tuple[str, ...]:
    """Return warnings for patterned-deposition requirements."""

    if step.kind is ProcessStepKind.PATTERNED_DEPOSITION and step.layer is None:
        return (f"Step {step.id} requires a layer reference.",)
    return ()

