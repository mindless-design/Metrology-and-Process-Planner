"""CSV/table import for simple process recipes."""

from __future__ import annotations

import csv
from io import StringIO
from typing import Any

from metrology_process_planner.domains.process.materials import (
    Material,
    material_catalog,
    resolve_material,
)
from metrology_process_planner.domains.process.recipe import ProcessRecipe
from metrology_process_planner.domains.process.recipe_import_helpers import (
    collect_materials,
    material_tuple,
    operation_kind,
    primary_material,
    step_id,
)
from metrology_process_planner.domains.process.recipe_import_models import RecipeImportDiagnostic
from metrology_process_planner.domains.process.step_specs import ThicknessSpec
from metrology_process_planner.domains.process.steps import ProcessStep
from metrology_process_planner.domains.units import UnitParseError, parse_length


def import_recipe_table(
    text: str,
    *,
    recipe_id: str = "imported-recipe",
    recipe_name: str = "Imported recipe",
    default_unit: str = "um",
) -> tuple[ProcessRecipe, tuple[RecipeImportDiagnostic, ...]]:
    """Import a simple CSV recipe table into a normalized process recipe."""

    diagnostics: list[RecipeImportDiagnostic] = []
    steps: list[ProcessStep] = []
    material_ids: list[str] = []
    reader = csv.DictReader(StringIO(text.strip()))
    for index, row in enumerate(reader, start=2):
        step = _step_from_row(row, index, default_unit, diagnostics)
        if step is None:
            continue
        steps.append(step)
        collect_materials(step, material_ids)
    materials = _materials_for(material_ids)
    recipe = ProcessRecipe(
        recipe_id,
        recipe_name,
        materials,
        tuple(steps),
        metadata={"import_source": "csv_table"},
    )
    return recipe, tuple(diagnostics)


def _step_from_row(
    row: dict[str, Any],
    row_number: int,
    default_unit: str,
    diagnostics: list[RecipeImportDiagnostic],
) -> ProcessStep | None:
    operation = _operation_text(row, row_number, diagnostics)
    if operation is None:
        return None
    kind = operation_kind(operation, row_number, diagnostics)
    if kind is None:
        return None
    imported_step_id = step_id(row, row_number)
    material = _material_from_row(row, row_number, diagnostics)
    thickness = _thickness(row, row_number, default_unit, diagnostics)
    return ProcessStep(
        imported_step_id,
        kind,
        material_id=primary_material(kind, material.id),
        thickness=thickness,
        target_material_ids=material_tuple(row.get("target")),
        stop_material_ids=material_tuple(row.get("stop")),
        notes=str(row.get("notes") or ""),
    )


def _operation_text(
    row: dict[str, Any],
    row_number: int,
    diagnostics: list[RecipeImportDiagnostic],
) -> str | None:
    operation = str(row.get("operation") or "").strip()
    if operation:
        return operation
    diagnostics.append(
        RecipeImportDiagnostic(
            "RECIPE_IMPORT_MISSING_OPERATION",
            "error",
            "Recipe row is missing an operation.",
            row_number,
            "operation",
            "Set operation to substrate, deposit, etch, strip, or note.",
        )
    )
    return None


def _material_from_row(
    row: dict[str, Any],
    row_number: int,
    diagnostics: list[RecipeImportDiagnostic],
) -> Material:
    material_text = str(row.get("material") or "").strip()
    material = resolve_material(material_text)
    if material.id == "unknown" and material_text:
        diagnostics.append(
            RecipeImportDiagnostic(
                "RECIPE_IMPORT_UNKNOWN_MATERIAL",
                "warning",
                f"Unknown material {row.get('material')} was mapped to unknown.",
                row_number,
                "material",
                "Use a catalog material id or alias, or add it to the material library.",
            )
        )
    return material


def _thickness(
    row: dict[str, Any],
    row_number: int,
    default_unit: str,
    diagnostics: list[RecipeImportDiagnostic],
) -> ThicknessSpec | None:
    raw = row.get("thickness")
    if raw in (None, ""):
        return None
    unit = str(row.get("unit") or default_unit)
    try:
        quantity = parse_length(
            {"value": raw, "unit": unit},
            default_unit=default_unit,
            allow_plain_angstrom=True,
        )
    except UnitParseError as exc:
        diagnostics.append(
            RecipeImportDiagnostic(
                "RECIPE_IMPORT_UNSUPPORTED_UNIT",
                "error",
                str(exc),
                row_number,
                "unit",
                "Use um, micron, nm, A, angstrom, mm, cm, or m.",
            )
        )
        return None
    if quantity.value_um < 0:
        diagnostics.append(
            RecipeImportDiagnostic(
                "RECIPE_IMPORT_NEGATIVE_THICKNESS",
                "error",
                "Thickness must be non-negative.",
                row_number,
                "thickness",
                "Enter zero or a positive thickness.",
            )
        )
    return ThicknessSpec(quantity.value_um, unit="um", display_unit=quantity.display_unit)


def _materials_for(material_ids: list[str]) -> tuple[Material, ...]:
    materials: dict[str, Material] = {}
    for item in material_ids or ["unknown"]:
        material = resolve_material(item)
        materials[material.id] = material
    return tuple(materials.values()) or (material_catalog()[-1],)
