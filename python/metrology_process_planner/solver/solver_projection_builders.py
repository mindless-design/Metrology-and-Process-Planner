"""Projection assembly helpers for hybrid solver results."""

from __future__ import annotations

from dataclasses import replace

from metrology_process_planner.domains.process.steps import ProcessStep
from metrology_process_planner.solver.geometry_kernel import GeometryKernel
from metrology_process_planner.solver.geometry_models import (
    RenderProjection,
    StackGeometry2D,
)
from metrology_process_planner.solver.solver_outputs import SolverDiagnostic, SolverInput
from metrology_process_planner.solver.solver_result_support import (
    material_metadata,
    projection_bounds,
)


def projection_from_geometry(
    kernel: GeometryKernel,
    geometry: StackGeometry2D,
    step: ProcessStep | None,
    label: str,
    diagnostics: tuple[SolverDiagnostic, ...],
    solver_input: SolverInput | None = None,
) -> RenderProjection:
    """Build a renderer-facing projection from solver geometry."""

    projection = kernel.make_render_projection(geometry)
    metadata = material_metadata(solver_input) if solver_input is not None else ()
    projection_id, source_step_id = _projection_source(label, step)
    return replace(
        projection,
        projection_id=projection_id,
        source_step_id=source_step_id,
        materials=metadata,
        physical_bounds=projection_bounds(geometry),
        units=_projection_units(solver_input),
        hidden_material_ids=_hidden_material_ids(metadata),
        changed_regions=projection.regions,
        material_regions=projection.regions,
        surface_profiles=(projection.surface,),
        void_regions=projection.void_regions,
        seam_regions=projection.seam_regions,
        pinch_off_regions=projection.pinch_off_regions,
        undercut_regions=projection.undercut_regions,
        tapered_regions=projection.tapered_regions,
        conformal_layers=projection.conformal_layers,
        warnings=_projection_warnings(diagnostics),
        thin_layer_hints=_thin_layer_hints(projection),
        compression_hints=_compression_hints(projection),
        approximation_notes=_approximation_notes(diagnostics),
    )


def _projection_source(label: str, step: ProcessStep | None) -> tuple[str, str]:
    source_step_id = step.id if step else ""
    return f"projection:{label}:{source_step_id or 'final'}", source_step_id


def _projection_units(solver_input: SolverInput | None) -> str:
    return solver_input.units if solver_input is not None else "um"


def _hidden_material_ids(metadata: tuple[dict[str, object], ...]) -> tuple[str, ...]:
    return tuple(str(item["id"]) for item in metadata if item.get("visible") is False)


def _projection_warnings(diagnostics: tuple[SolverDiagnostic, ...]) -> tuple[str, ...]:
    return tuple(item.code for item in diagnostics if item.severity != "info")


def _approximation_notes(diagnostics: tuple[SolverDiagnostic, ...]) -> tuple[str, ...]:
    return tuple(item.message for item in diagnostics if "APPROXIM" in item.code)


def _thin_layer_hints(projection: RenderProjection) -> dict[str, object]:
    layers = [layer for layer in projection.conformal_layers if layer.thin_layer_flag]
    return {
        "conformal_layer_ids": tuple(layer.material_id for layer in layers),
        "minimum_visual_thickness_recommended": bool(layers),
        "exaggeration_note_required": bool(layers),
    }


def _compression_hints(projection: RenderProjection) -> dict[str, object]:
    return {
        "full_stack_compression_supported": True,
        "preserve_regions": tuple(layer.material_id for layer in projection.conformal_layers),
        "reason": "projection carries physical bounds and thin-layer hints",
    }
