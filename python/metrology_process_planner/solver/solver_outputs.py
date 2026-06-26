"""Inputs, outputs, diagnostics, and compatibility seams for the solver."""

from __future__ import annotations

from dataclasses import dataclass

from metrology_process_planner.domains.process.recipe import ProcessRecipe
from metrology_process_planner.solver.geometry_models import (
    CrossSectionProfile,
    CutlineSample,
    GeometrySnapshot,
    PointSample,
    RenderProjection,
    StackGeometry2D,
)
from metrology_process_planner.solver.solver_profiles import SolverOptions


@dataclass(frozen=True)
class SolverDiagnostic:
    """Structured diagnostic emitted by the process solver."""

    severity: str
    code: str
    step_id: str
    message: str
    technical_details: str = ""
    suggested_repair: str = ""
    output_usable: bool = True
    diagnostic_id: str = ""
    step_name: str = ""

    def __post_init__(self) -> None:
        if not self.diagnostic_id:
            identifier = f"{self.step_id or 'solver'}:{self.code}"
            object.__setattr__(self, "diagnostic_id", identifier)


@dataclass(frozen=True)
class ProcessFrame:
    """Process-flow frame captured after one recipe step."""

    step_id: str
    title: str
    profile: CrossSectionProfile
    projection: RenderProjection | None = None
    metadata: dict[str, str] | None = None
    frame_id: str = ""
    step_index: int = -1
    step_name: str = ""
    operation_type: str = ""
    stack_signature: str = ""
    changed_from_previous: bool = True
    changed_regions: tuple[object, ...] = ()
    diagnostics: tuple[SolverDiagnostic, ...] = ()
    variant_label: str = "target"
    render_projection: RenderProjection | None = None

    def __post_init__(self) -> None:
        if self.metadata is None:
            object.__setattr__(self, "metadata", {})
        if not self.frame_id:
            object.__setattr__(self, "frame_id", f"frame:{self.step_id}")
        if not self.step_name:
            object.__setattr__(self, "step_name", self.title)
        if self.render_projection is None:
            object.__setattr__(self, "render_projection", self.projection)


@dataclass(frozen=True)
class SolverInput:
    """Input contract for the hybrid process solver."""

    recipe: ProcessRecipe
    options: SolverOptions = SolverOptions()
    sample_count: int = 201
    geometry_context: object | None = None
    requested_outputs: tuple[str, ...] = ("physical_cross_section",)
    units: str = "um"
    variant_selection: str = "target"
    source_geometry_metadata: dict[str, object] | None = None
    backend_id: str = "sampled_geometry"

    def __post_init__(self) -> None:
        if self.source_geometry_metadata is None:
            object.__setattr__(self, "source_geometry_metadata", {})


@dataclass(frozen=True)
class SolverResult:
    """Output contract from the hybrid cross-section solver."""

    frames: tuple[ProcessFrame, ...]
    diagnostics: tuple[SolverDiagnostic, ...] = ()
    point_samples: tuple[PointSample, ...] = ()
    cutline_samples: tuple[CutlineSample, ...] = ()
    snapshots: tuple[GeometrySnapshot, ...] = ()
    variant_label: str = "target"
    solver_id: str = "hybrid_cross_section_solver"
    backend_id: str = "sampled_geometry"
    backend_version: str = "v1"
    input_hash: str = ""
    recipe_id: str = ""
    final_stack: StackGeometry2D | None = None
    render_projections: tuple[RenderProjection, ...] = ()
    approximation_notes: tuple[str, ...] = ()
    metrics: dict[str, object] | None = None
    units: str = "um"
    material_metadata: tuple[dict[str, object], ...] = ()

    def __post_init__(self) -> None:
        if self.metrics is None:
            object.__setattr__(self, "metrics", {})

    @property
    def warnings(self) -> tuple[str, ...]:
        """Compatibility warning strings for older callers."""

        return tuple(item.message for item in self.diagnostics if item.severity != "info")


@dataclass(frozen=True)
class RecipeToPyxsPlan:
    """Mapping summary from Process Planner recipe operations to pyxs-style ops."""

    mapped_step_ids: tuple[str, ...]
    internal_only_step_ids: tuple[str, ...]
    notes: tuple[str, ...] = ()


@dataclass(frozen=True)
class PyxsComparisonRequest:
    """Request to compare a Process Planner recipe against a pyxs implementation."""

    recipe: ProcessRecipe
    plan: RecipeToPyxsPlan
    tolerance: float = 1e-6
