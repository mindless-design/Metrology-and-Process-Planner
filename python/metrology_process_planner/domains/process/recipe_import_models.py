"""Models for recipe table import diagnostics."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class RecipeImportDiagnostic:
    """Structured row/field diagnostic for imported recipe tables."""

    code: str
    severity: str
    message: str
    row_number: int = 0
    field: str = ""
    repair_suggestion: str = ""
