"""Renderer-facing projection contract validation."""

from __future__ import annotations

from dataclasses import dataclass

from metrology_process_planner.solver.geometry_models import RenderProjection
from metrology_process_planner.solver.solver_outputs import SolverDiagnostic

PROJECTION_TYPES = (
    "physical_cross_section",
    "illustrative_cross_section",
    "profilometry_surface",
    "fib_full_stack",
    "process_flow_frame",
    "point_stack",
)


@dataclass(frozen=True)
class ProjectionValidationResult:
    """Validation result for renderer-facing projections."""

    diagnostics: tuple[SolverDiagnostic, ...] = ()

    @property
    def passed(self) -> bool:
        """Return whether the projection is renderer-compatible."""

        return not self.diagnostics


def validate_render_projection(projection: RenderProjection) -> ProjectionValidationResult:
    """Validate that a render projection is complete enough for renderers."""

    diagnostics: list[SolverDiagnostic] = []
    material_ids = _material_ids(projection)
    diagnostics.extend(_projection_metadata_diagnostics(projection))
    diagnostics.extend(_material_order_diagnostics(projection, material_ids))
    diagnostics.extend(_region_diagnostics(projection, material_ids))
    return ProjectionValidationResult(tuple(diagnostics))


def _projection_metadata_diagnostics(
    projection: RenderProjection,
) -> tuple[SolverDiagnostic, ...]:
    diagnostics: list[SolverDiagnostic] = []
    if projection.projection_type not in PROJECTION_TYPES:
        diagnostics.append(_diagnostic("Unsupported render projection type."))
    if not projection.units:
        diagnostics.append(_diagnostic("Render projection is missing units."))
    if projection.physical_bounds is not None and not _valid_bounds(projection.physical_bounds):
        diagnostics.append(_diagnostic("Render projection physical bounds are invalid."))
    if not projection.regions and not _has_intentional_empty_diagnostic(projection):
        diagnostics.append(_diagnostic("Render projection has no material geometry."))
    return tuple(diagnostics)


def _material_order_diagnostics(
    projection: RenderProjection,
    material_ids: set[str],
) -> tuple[SolverDiagnostic, ...]:
    diagnostics: list[SolverDiagnostic] = []
    for material_id in projection.material_order:
        if material_id not in material_ids:
            diagnostics.append(_diagnostic(f"Material id has no display metadata: {material_id}."))
    return tuple(diagnostics)


def _region_diagnostics(
    projection: RenderProjection,
    material_ids: set[str],
) -> tuple[SolverDiagnostic, ...]:
    diagnostics: list[SolverDiagnostic] = []
    for region in projection.regions:
        if region.material_id not in material_ids:
            diagnostics.append(
                _diagnostic(f"Region material id is unresolved: {region.material_id}.")
            )
        if region.x_max <= region.x_min or region.z_max <= region.z_min:
            diagnostics.append(_diagnostic("Render projection contains invalid region bounds."))
    return tuple(diagnostics)


def _material_ids(projection: RenderProjection) -> set[str]:
    ids = {str(item.get("id")) for item in projection.materials if item.get("id")}
    ids.update(projection.material_order)
    return ids


def _valid_bounds(bounds: tuple[float, float, float, float]) -> bool:
    x_min, x_max, z_min, z_max = bounds
    return x_max > x_min and z_max >= z_min


def _has_intentional_empty_diagnostic(projection: RenderProjection) -> bool:
    return any(
        code in projection.warnings
        for code in ("EMPTY_MASK", "RENDER_PROJECTION_INCOMPLETE")
    )


def _diagnostic(message: str) -> SolverDiagnostic:
    return SolverDiagnostic(
        "error",
        "RENDER_PROJECTION_INCOMPLETE",
        "",
        message,
        suggested_repair="Rebuild the projection from a validated SolverResult.",
        output_usable=False,
    )
