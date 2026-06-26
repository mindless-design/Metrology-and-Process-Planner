"""Structured process recipe validation service."""

from __future__ import annotations

from typing import TYPE_CHECKING

from metrology_process_planner.domains.process.validation_materials import (
    material_messages,
    unused_material_messages,
)
from metrology_process_planner.domains.process.validation_messages import RecipeValidationMessage
from metrology_process_planner.domains.process.validation_steps import (
    recipe_shape_messages,
    step_messages,
)
from metrology_process_planner.domains.process.validation_windows import window_messages

if TYPE_CHECKING:
    from metrology_process_planner.domains.process.recipe import ProcessRecipe


class RecipeValidationService:
    """Validate a process recipe into structured, clickable messages."""

    def validate(self, recipe: ProcessRecipe) -> tuple[RecipeValidationMessage, ...]:
        """Return structured validation messages for a recipe."""

        material_ids = {material.id for material in recipe.materials}
        return (
            material_messages(recipe.materials)
            + step_messages(recipe.steps, material_ids)
            + window_messages(recipe.process_windows)
            + recipe_shape_messages(recipe.steps)
            + unused_material_messages(recipe.materials, recipe.steps)
        )
