"""Solver-input normalization helpers for process-output workflows."""

from __future__ import annotations

from dataclasses import replace

from metrology_process_planner.domains.process import (
    ProcessRecipe,
    ProcessStep,
    ProcessWindow,
    ThicknessSpec,
)


def normalized_recipe(recipe: ProcessRecipe) -> ProcessRecipe:
    """Return a recipe with solver-facing length units normalized."""

    return replace(
        recipe,
        steps=tuple(_normalized_step(step) for step in recipe.steps),
        process_windows=tuple(_normalized_window(window) for window in recipe.process_windows),
    )


def _normalized_step(step: ProcessStep) -> ProcessStep:
    if step.thickness is None:
        return step
    thickness = ThicknessSpec(
        step.thickness.target,
        lower=step.thickness.lower,
        upper=step.thickness.upper,
        unit="um",
        display_unit=step.thickness.display_unit or step.thickness.unit,
    )
    return replace(step, thickness=thickness)


def _normalized_window(window: ProcessWindow) -> ProcessWindow:
    return ProcessWindow(
        window.name,
        window.lower,
        window.target,
        window.upper,
        unit="um",
        display_unit=window.display_unit or window.unit,
    )
