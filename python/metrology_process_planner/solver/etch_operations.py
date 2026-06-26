"""Etch operation executors for the hybrid cross-section solver."""

from __future__ import annotations

from metrology_process_planner.domains.process.steps import MaskPolarity, ProcessStep
from metrology_process_planner.solver.etch_diagnostics import etch_depth_diagnostics
from metrology_process_planner.solver.geometry_kernel import GeometryKernel
from metrology_process_planner.solver.geometry_models import StackGeometry2D
from metrology_process_planner.solver.operation_helpers import (
    _diag,
    _etch_profile,
    _legacy_and_contract_diagnostics,
    _required,
)
from metrology_process_planner.solver.operation_results import OperationResult
from metrology_process_planner.solver.solver_outputs import SolverDiagnostic
from metrology_process_planner.solver.solver_profiles import EtchProfile


class DirectionalEtchOperation:
    """Directional top-down etch executor."""

    def execute(
        self,
        kernel: GeometryKernel,
        geometry: StackGeometry2D | None,
        step: ProcessStep,
    ) -> OperationResult:
        """Etch target materials top-down until depth or blocker stops removal."""

        source = _required(geometry)
        profile = _etch_profile(step)
        depth = profile.depth * profile.overetch_factor
        return OperationResult(
            kernel.etch_directional(source, profile),
            etch_depth_diagnostics(source, profile, step.id, depth),
        )


class IsotropicEtchOperation:
    """Isotropic exposed-boundary etch executor."""

    def execute(
        self,
        kernel: GeometryKernel,
        geometry: StackGeometry2D | None,
        step: ProcessStep,
    ) -> OperationResult:
        """Etch target materials with lateral attack diagnostics."""

        source = _required(geometry)
        profile = _etch_profile(step)
        diagnostics = list(_legacy_and_contract_diagnostics(
            "warning", step.id, "ISOTROPIC_UNDERCUT", "ISOTROPIC_UNDERCUT_APPROXIMATED"
        ))
        if profile.stop_materials:
            diagnostics.append(_diag("info", "ISOTROPIC_ETCH_STOPPED_ON_BLOCKER", step.id))
        return OperationResult(
            kernel.etch_isotropic(source, profile),
            tuple(diagnostics) + etch_depth_diagnostics(source, profile, step.id, profile.depth),
        )


class TaperedEtchOperation:
    """Tapered etch approximation executor."""

    def execute(
        self,
        kernel: GeometryKernel,
        geometry: StackGeometry2D | None,
        step: ProcessStep,
    ) -> OperationResult:
        """Etch target materials using a tapered approximation."""

        source = _required(geometry)
        profile = _etch_profile(step)
        depth = profile.depth * profile.overetch_factor
        invalid_angle = (
            profile.sidewall_angle_deg is not None
            and not 0.0 < profile.sidewall_angle_deg < 90.0
        )
        if invalid_angle:
            return OperationResult(
                source,
                (
                    SolverDiagnostic(
                        "error",
                        "TAPERED_ETCH_INVALID_ANGLE",
                        step.id,
                        "Tapered etch sidewall angle must be between 0 and 90 degrees.",
                        output_usable=False,
                    ),
                ),
            )
        diagnostics = list(_legacy_and_contract_diagnostics(
            "info", step.id, "TAPERED_PROFILE_APPROXIMATION", "TAPERED_PROFILE_APPROXIMATED"
        ))
        if profile.sidewall_angle_deg is not None and _bottom_closed(source, profile):
            diagnostics.append(_diag("warning", "TAPERED_ETCH_BOTTOM_CLOSED", step.id))
        if profile.stop_materials:
            diagnostics.append(_diag("info", "TAPERED_ETCH_STOPPED_ON_BLOCKER", step.id))
        return OperationResult(
            kernel.etch_tapered(source, profile),
            tuple(diagnostics) + etch_depth_diagnostics(source, profile, step.id, depth),
        )


def _bottom_closed(geometry: StackGeometry2D, profile: EtchProfile) -> bool:
    targets = [
        column.x
        for column in geometry.columns
        if _is_profile_masked(column.x, profile)
        and column.intervals
        and (not profile.targets or column.intervals[-1].material_id in profile.targets)
    ]
    if len(targets) < 2 or profile.sidewall_angle_deg is None:
        return False
    from math import radians, tan

    top_width = max(targets) - min(targets)
    recession = profile.depth * tan(radians(90.0 - profile.sidewall_angle_deg))
    return top_width - 2 * recession + profile.bottom_cd_bias <= 0.0


def _is_profile_masked(x: float, profile: EtchProfile) -> bool:
    inside = any(interval.contains(x) for interval in profile.mask) if profile.mask else True
    if profile.mask_polarity == MaskPolarity.INVERTED.value:
        return not inside
    return inside
