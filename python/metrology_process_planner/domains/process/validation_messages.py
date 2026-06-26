"""Structured process recipe validation message models."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class RecipeValidationMessage:
    """Structured recipe validation message shared by UI, solver, and diagnostics."""

    id: str
    severity: str
    source: str
    message: str
    related_material_id: str = ""
    related_step_id: str = ""
    related_layer: str = ""
    technical_details: str = ""
    repair_suggestion: str = ""


def recipe_validation_message(
    message_id: str,
    severity: str,
    source: str,
    message: str,
    *,
    material_id: str = "",
    step_id: str = "",
    layer: str = "",
    technical_details: str = "",
    repair: str = "",
) -> RecipeValidationMessage:
    """Build one structured recipe validation message."""

    return RecipeValidationMessage(
        message_id,
        severity,
        source,
        message,
        material_id,
        step_id,
        layer,
        technical_details,
        repair,
    )
