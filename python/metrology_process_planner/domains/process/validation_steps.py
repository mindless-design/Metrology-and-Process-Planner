"""Step-level structured process recipe validation."""

from __future__ import annotations

from metrology_process_planner.domains.process.steps import ProcessStep, ProcessStepKind
from metrology_process_planner.domains.process.validation_messages import (
    RecipeValidationMessage,
    recipe_validation_message,
)

DEPOSITION_KINDS = {
    ProcessStepKind.BLANKET_DEPOSITION,
    ProcessStepKind.PATTERNED_DEPOSITION,
    ProcessStepKind.CONFORMAL_DEPOSITION,
    ProcessStepKind.CONFORMAL_COATING,
}
LAYER_REQUIRED_KINDS = {
    ProcessStepKind.PATTERNED_DEPOSITION,
    ProcessStepKind.DIRECTIONAL_ETCH,
    ProcessStepKind.ISOTROPIC_ETCH,
    ProcessStepKind.TAPERED_ETCH,
}


def step_messages(
    steps: tuple[ProcessStep, ...],
    material_ids: set[str],
) -> tuple[RecipeValidationMessage, ...]:
    """Return structured validation messages for recipe steps."""

    messages: list[RecipeValidationMessage] = []
    seen: set[str] = set()
    for step in steps:
        messages.extend(_step_identity_messages(step, seen))
        seen.add(step.id)
        messages.extend(_step_material_messages(step, material_ids))
        messages.extend(_step_dimension_messages(step))
        messages.extend(_step_layer_messages(step))
        messages.extend(_disabled_step_messages(step))
    if not steps:
        messages.append(_recipe_steps_empty_message())
    return tuple(messages)

def recipe_shape_messages(steps: tuple[ProcessStep, ...]) -> tuple[RecipeValidationMessage, ...]:
    """Return recipe-level shape messages tied to process step ordering."""

    if not steps or steps[0].kind is ProcessStepKind.SUBSTRATE:
        return ()
    return (
        recipe_validation_message(
            "recipe-missing-substrate",
            "warning",
            "recipe",
            "Recipe has no substrate/init step.",
            repair="Add an Initialize substrate / wafer step at the start.",
        ),
    )


def requires_material(step: ProcessStep) -> bool:
    """Return whether a process step kind requires a primary material."""

    return step.kind in {
        ProcessStepKind.SUBSTRATE,
        ProcessStepKind.BLANKET_DEPOSITION,
        ProcessStepKind.PATTERNED_DEPOSITION,
        ProcessStepKind.CONFORMAL_COATING,
        ProcessStepKind.CONFORMAL_DEPOSITION,
    }

def _step_identity_messages(
    step: ProcessStep,
    seen: set[str],
) -> tuple[RecipeValidationMessage, ...]:
    if not step.id:
        return (
            recipe_validation_message(
                "step-missing-id",
                "blocking",
                "step",
                "Process step is missing an ID.",
                step_id=step.id,
                repair="Assign a stable step ID.",
            ),
        )
    if step.id in seen:
        return (
            recipe_validation_message(
                f"step-duplicate-{step.id}",
                "blocking",
                "step",
                f"Duplicate process step ID: {step.id}.",
                step_id=step.id,
                repair="Rename one process step to a unique ID.",
            ),
        )
    return ()

def _step_material_messages(
    step: ProcessStep,
    material_ids: set[str],
) -> tuple[RecipeValidationMessage, ...]:
    messages: list[RecipeValidationMessage] = []
    if requires_material(step) and not step.material_id:
        messages.append(_missing_step_material_message(step))
    if step.material_id and step.material_id not in material_ids:
        messages.append(_unknown_step_material_message(step, step.material_id))
    for target_id in step.target_material_ids:
        if target_id not in material_ids:
            messages.append(_unknown_target_material_message(step, target_id))
    return tuple(messages)

def _step_dimension_messages(step: ProcessStep) -> tuple[RecipeValidationMessage, ...]:
    messages: list[RecipeValidationMessage] = []
    if step.kind in DEPOSITION_KINDS and step.thickness is None:
        messages.append(
            recipe_validation_message(
                f"step-thickness-required-{step.id}",
                "error",
                "step",
                f"Step {step.id} requires a thickness.",
                step_id=step.id,
                repair="Add a target thickness.",
            )
        )
    if step.thickness is not None:
        messages.extend(_thickness_warning_messages(step))
    return tuple(messages)


def _thickness_warning_messages(step: ProcessStep) -> tuple[RecipeValidationMessage, ...]:
    if step.thickness is None:
        return ()
    return tuple(
        recipe_validation_message(
            f"step-thickness-{step.id}-{index}",
            "error",
            "step",
            f"Step {step.id}: {warning}",
            step_id=step.id,
            repair="Fix the thickness limits.",
        )
        for index, warning in enumerate(step.thickness.validate())
    )


def _step_layer_messages(step: ProcessStep) -> tuple[RecipeValidationMessage, ...]:
    if step.kind not in LAYER_REQUIRED_KINDS or step.layer is not None:
        return ()
    return (
        recipe_validation_message(
            f"step-layer-required-{step.id}",
            "error",
            "layer",
            f"Step {step.id} requires a layer reference.",
            step_id=step.id,
            repair="Choose a KLayout layer/mask for this patterned operation.",
        ),
    )


def _disabled_step_messages(step: ProcessStep) -> tuple[RecipeValidationMessage, ...]:
    if step.enabled:
        return ()
    return (
        recipe_validation_message(
            f"step-disabled-{step.id}",
            "info",
            "step",
            f"Step {step.id} is disabled.",
            step_id=step.id,
            repair="Enable the step if it should affect solver outputs.",
        ),
    )


def _missing_step_material_message(step: ProcessStep) -> RecipeValidationMessage:
    return recipe_validation_message(
        f"step-material-required-{step.id}",
        "error",
        "step",
        f"Step {step.id} requires a material.",
        step_id=step.id,
        repair="Choose a material for this operation.",
    )


def _unknown_step_material_message(step: ProcessStep, material_id: str) -> RecipeValidationMessage:
    return recipe_validation_message(
        f"step-material-unknown-{step.id}-{material_id}",
        "blocking",
        "step",
        f"Step {step.id} references unknown material {material_id}.",
        material_id=material_id,
        step_id=step.id,
        repair="Create the material or change the step reference.",
    )


def _unknown_target_material_message(step: ProcessStep, target_id: str) -> RecipeValidationMessage:
    return recipe_validation_message(
        f"step-target-unknown-{step.id}-{target_id}",
        "blocking",
        "step",
        f"Step {step.id} targets unknown material {target_id}.",
        material_id=target_id,
        step_id=step.id,
        repair="Create the target material or update the target list.",
    )


def _recipe_steps_empty_message() -> RecipeValidationMessage:
    return recipe_validation_message(
        "recipe-steps-empty",
        "blocking",
        "recipe",
        "Recipe must define at least one process step.",
        repair="Add a process step card.",
    )
