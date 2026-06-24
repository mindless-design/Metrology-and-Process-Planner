"""Inputs, outputs, diagnostics, and compatibility seams for the solver."""

from __future__ import annotations

from dataclasses import dataclass

from metrology_process_planner.domains.process.geometry_models import (
    CrossSectionProfile,
    CutlineSample,
    GeometrySnapshot,
    PointSample,
    RenderProjection,
)
from metrology_process_planner.domains.process.recipe import ProcessRecipe
from metrology_process_planner.domains.process.solver_profiles import SolverOptions


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


@dataclass(frozen=True)
class ProcessFrame:
    """Process-flow frame captured after one recipe step."""

    step_id: str
    title: str
    profile: CrossSectionProfile
    projection: RenderProjection | None = None
    metadata: dict[str, str] | None = None

    def __post_init__(self) -> None:
        if self.metadata is None:
            object.__setattr__(self, "metadata", {})


@dataclass(frozen=True)
class SolverInput:
    """Input contract for the hybrid process solver."""

    recipe: ProcessRecipe
    options: SolverOptions = SolverOptions()
    sample_count: int = 201


@dataclass(frozen=True)
class SolverResult:
    """Output contract from the hybrid cross-section solver."""

    frames: tuple[ProcessFrame, ...]
    diagnostics: tuple[SolverDiagnostic, ...] = ()
    point_samples: tuple[PointSample, ...] = ()
    cutline_samples: tuple[CutlineSample, ...] = ()
    snapshots: tuple[GeometrySnapshot, ...] = ()
    variant_label: str = "target"

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
