"""Helper functions for recipe table import."""

from __future__ import annotations

from typing import Any

from metrology_process_planner.domains.process.materials import resolve_material
from metrology_process_planner.domains.process.recipe_import_models import (
    RecipeImportDiagnostic,
)
from metrology_process_planner.domains.process.steps import ProcessStep, ProcessStepKind


def operation_kind(
    operation: str,
    row_number: int,
    diagnostics: list[RecipeImportDiagnostic],
) -> ProcessStepKind | None:
    """Return a supported process-step kind for an imported operation token."""

    kind = _operation_map().get(operation.strip().lower().replace(" ", "_"))
    if kind is None:
        diagnostics.append(
            RecipeImportDiagnostic(
                "RECIPE_IMPORT_UNSUPPORTED_OPERATION",
                "error",
                f"Unsupported operation {operation}.",
                row_number,
                "operation",
                "Use substrate, deposit, etch, strip, planarize, cmp, or note.",
            )
        )
    return kind


def material_tuple(value: Any) -> tuple[str, ...]:
    """Return resolved material ids from a semicolon-delimited import field."""

    raw = str(value or "").strip()
    if not raw:
        return ()
    return tuple(resolve_material(item.strip()).id for item in raw.split(";") if item.strip())


def collect_materials(step: ProcessStep, material_ids: list[str]) -> None:
    """Append every material reference used by an imported step."""

    if step.material_id:
        material_ids.append(step.material_id)
    material_ids.extend(step.target_material_ids)
    material_ids.extend(step.stop_material_ids)


def step_id(row: dict[str, Any], row_number: int) -> str:
    """Return a stable imported step id."""

    raw = str(row.get("step") or "").strip()
    if raw:
        if raw.startswith("step-"):
            return raw
        if raw.isdigit():
            return f"step-{int(float(raw)):03d}"
        return raw
    return f"step-{row_number - 1:03d}"


def primary_material(kind: ProcessStepKind, material_id: str) -> str | None:
    """Return the primary material when an operation owns one."""

    if kind in {
        ProcessStepKind.SUBSTRATE,
        ProcessStepKind.BLANKET_DEPOSITION,
        ProcessStepKind.PATTERNED_DEPOSITION,
        ProcessStepKind.CONFORMAL_COATING,
        ProcessStepKind.CONFORMAL_DEPOSITION,
    }:
        return material_id
    return None


def _operation_map() -> dict[str, ProcessStepKind]:
    return {
        "substrate": ProcessStepKind.SUBSTRATE,
        "init": ProcessStepKind.SUBSTRATE,
        "initialize": ProcessStepKind.SUBSTRATE,
        "deposit": ProcessStepKind.BLANKET_DEPOSITION,
        "deposition": ProcessStepKind.BLANKET_DEPOSITION,
        "blanket_deposition": ProcessStepKind.BLANKET_DEPOSITION,
        "coat": ProcessStepKind.CONFORMAL_COATING,
        "coating": ProcessStepKind.CONFORMAL_COATING,
        "etch": ProcessStepKind.DIRECTIONAL_ETCH,
        "directional_etch": ProcessStepKind.DIRECTIONAL_ETCH,
        "strip": ProcessStepKind.DIRECTIONAL_ETCH,
        "planarize": ProcessStepKind.PLANARIZATION,
        "cmp": ProcessStepKind.CMP_PLANARIZATION,
        "note": ProcessStepKind.ANNOTATION_ONLY,
    }
