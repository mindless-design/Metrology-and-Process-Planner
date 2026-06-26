"""Private helpers for process operation executors."""

from __future__ import annotations

from metrology_process_planner.domains.process.steps import ProcessStep
from metrology_process_planner.solver.geometry_models import MaskInterval, StackGeometry2D
from metrology_process_planner.solver.solver_outputs import SolverDiagnostic
from metrology_process_planner.solver.solver_profiles import (
    ConformalProfile,
    EtchProfile,
    PlanarizationProfile,
)


def _required(geometry: StackGeometry2D | None) -> StackGeometry2D:
    if geometry is None:
        raise ValueError("Process geometry has not been initialized.")
    return geometry


def _thickness(step: ProcessStep, default: float = 0.0) -> float:
    return step.thickness.target if step.thickness is not None else default


def _etch_profile(step: ProcessStep) -> EtchProfile:
    if step.etch_profile is not None:
        return EtchProfile(
            depth=step.etch_profile.depth,
            targets=step.etch_profile.targets,
            stop_materials=step.etch_profile.stop_materials,
            overetch_factor=step.etch_profile.overetch_factor,
            lateral_attack=step.etch_profile.lateral_attack,
            sidewall_angle_deg=step.etch_profile.sidewall_angle_deg,
            top_cd_bias=step.etch_profile.top_cd_bias,
            bottom_cd_bias=step.etch_profile.bottom_cd_bias,
            step_id=step.id,
            mask=step.mask_intervals,
            mask_polarity=step.mask_polarity.value,
        )
    parameters = dict(step.parameters or {})
    return EtchProfile(
        depth=_thickness(step),
        targets=step.target_material_ids,
        stop_materials=step.stop_material_ids,
        overetch_factor=_float_parameter(parameters, "overetch_factor", "overetch", 1.0),
        lateral_attack=_float_parameter(parameters, "lateral_attack", "lateral_distance", 0.0),
        sidewall_angle_deg=_optional_float(parameters.get("sidewall_angle_deg")),
        top_cd_bias=float(parameters.get("top_cd_bias", 0.0)),
        bottom_cd_bias=float(parameters.get("bottom_cd_bias", 0.0)),
        step_id=step.id,
        mask=step.mask_intervals,
        mask_polarity=step.mask_polarity.value,
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


def _conformal_profile(step: ProcessStep) -> ConformalProfile:
    if step.conformal_profile is not None:
        return step.conformal_profile
    parameters = dict(step.parameters or {})
    return ConformalProfile(
        top_coverage=_float_parameter(parameters, "top_coverage", "top_coverage_factor", 1.0),
        sidewall_coverage=float(
            parameters.get("sidewall_coverage", parameters.get("sidewall_coverage_factor", 1.0))
        ),
        bottom_coverage=float(
            parameters.get("bottom_coverage", parameters.get("bottom_coverage_factor", 1.0))
        ),
    )


def _optional_float(value: object) -> float | None:
    if value is None or value == "":
        return None
    return float(str(value))


def _float_parameter(
    parameters: dict[str, object],
    primary: str,
    fallback: str,
    default: float,
) -> float:
    return float(str(parameters.get(primary, parameters.get(fallback, default))))


def _legacy_and_contract_diagnostics(
    severity: str,
    step_id: str,
    legacy_code: str,
    contract_code: str,
) -> tuple[SolverDiagnostic, SolverDiagnostic]:
    return (_diag(severity, legacy_code, step_id), _diag(severity, contract_code, step_id))


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
