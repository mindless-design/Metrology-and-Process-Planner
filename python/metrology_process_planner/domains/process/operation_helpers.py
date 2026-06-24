"""Private helpers for process operation executors."""

from __future__ import annotations

from metrology_process_planner.domains.process.geometry_models import MaskInterval, StackGeometry2D
from metrology_process_planner.domains.process.solver_outputs import SolverDiagnostic
from metrology_process_planner.domains.process.solver_profiles import (
    ConformalProfile,
    EtchProfile,
    PlanarizationProfile,
)
from metrology_process_planner.domains.process.steps import ProcessStep


def _required(geometry: StackGeometry2D | None) -> StackGeometry2D:
    if geometry is None:
        raise ValueError("Process geometry has not been initialized.")
    return geometry


def _thickness(step: ProcessStep, default: float = 0.0) -> float:
    return step.thickness.target if step.thickness is not None else default


def _etch_profile(step: ProcessStep) -> EtchProfile:
    if step.etch_profile is not None:
        return step.etch_profile
    return EtchProfile(
        depth=_thickness(step),
        targets=step.target_material_ids,
        stop_materials=step.stop_material_ids,
    )


def _planar_profile(step: ProcessStep) -> PlanarizationProfile:
    return step.planarization_profile or PlanarizationProfile(target_height=_thickness(step))


def _diag(severity: str, code: str, step_id: str) -> SolverDiagnostic:
    return SolverDiagnostic(
        severity,
        code,
        step_id,
        code.replace("_", " ").title(),
        output_usable=True,
    )


def _pinch_off_possible(
    geometry: StackGeometry2D,
    mask: tuple[MaskInterval, ...],
    thickness: float,
    profile: ConformalProfile,
) -> bool:
    intervals = mask or ()
    gap_widths = [interval.width for interval in intervals]
    if not gap_widths:
        gap_widths = [_sample_width(geometry)]
    growth = 2 * thickness * profile.sidewall_coverage
    return any(width <= growth for width in gap_widths)


def _sample_width(geometry: StackGeometry2D) -> float:
    if len(geometry.columns) <= 1:
        return 1.0
    return abs(geometry.columns[1].x - geometry.columns[0].x)
