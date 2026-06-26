"""Support helpers for assembling hybrid solver results."""

from __future__ import annotations

import hashlib
import json

from metrology_process_planner.domains.process.render_contract import validate_render_projection
from metrology_process_planner.solver.geometry_models import (
    RenderProjection,
    StackGeometry2D,
)
from metrology_process_planner.solver.solver_outputs import (
    ProcessFrame,
    SolverDiagnostic,
    SolverInput,
)


def input_hash(solver_input: SolverInput) -> str:
    """Return a stable hash for solver input provenance."""

    payload = {
        "recipe": solver_input.recipe.to_dict(),
        "options": repr(solver_input.options),
        "units": solver_input.units,
        "variant": solver_input.variant_selection,
        "backend": solver_input.backend_id,
    }
    return hashlib.sha256(json.dumps(payload, sort_keys=True).encode("utf-8")).hexdigest()


def metrics(geometry: StackGeometry2D | None, frames: list[ProcessFrame]) -> dict[str, object]:
    """Return compact solver execution metrics."""

    return {
        "column_count": len(geometry.columns) if geometry is not None else 0,
        "frame_count": len(frames),
    }


def projection_bounds(geometry: StackGeometry2D) -> tuple[float, float, float, float]:
    """Return physical bounds for a stack projection."""

    xs = [column.x for column in geometry.columns]
    tops = [column.top for column in geometry.columns]
    bottoms = [
        interval.z_min for column in geometry.columns for interval in column.intervals
    ] or [0.0]
    return (min(xs), max(xs), min(bottoms), max(tops) if tops else 0.0)


def material_metadata(solver_input: SolverInput | None) -> tuple[dict[str, object], ...]:
    """Return serialized material metadata for render projections."""

    if solver_input is None or solver_input.recipe is None:
        return ()
    return tuple(material.to_dict() for material in solver_input.recipe.materials)


def strict_projection_diagnostics(
    projections: tuple[RenderProjection, ...],
) -> tuple[SolverDiagnostic, ...]:
    """Validate generated render projections under strict solver mode."""

    diagnostics: list[SolverDiagnostic] = []
    for projection in projections:
        diagnostics.extend(validate_render_projection(projection).diagnostics)
    return tuple(diagnostics)
