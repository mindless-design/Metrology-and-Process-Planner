"""Modular operation executors for the hybrid cross-section solver."""

from __future__ import annotations

from typing import Protocol

from metrology_process_planner.domains.process.steps import ProcessStep
from metrology_process_planner.solver.geometry_kernel import GeometryKernel
from metrology_process_planner.solver.geometry_models import StackGeometry2D
from metrology_process_planner.solver.operation_helpers import (
    _conformal_profile,
    _diag,
    _legacy_and_contract_diagnostics,
    _pinch_off_possible,
    _planar_profile,
    _required,
    _thickness,
)
from metrology_process_planner.solver.operation_results import OperationResult


class ProcessOperation(Protocol):
    """Process operation executor contract."""

    def execute(
        self,
        kernel: GeometryKernel,
        geometry: StackGeometry2D | None,
        step: ProcessStep,
    ) -> OperationResult:
        """Execute one recipe step."""


class SubstrateOperation:
    """Create initial substrate geometry."""

    def execute(
        self,
        kernel: GeometryKernel,
        geometry: StackGeometry2D | None,
        step: ProcessStep,
    ) -> OperationResult:
        """Create the starting substrate stack."""

        return OperationResult(
            kernel.initialize_substrate(str(step.material_id), _thickness(step, 1.0))
        )


class BlanketDepositOperation:
    """Topography-following blanket deposition."""

    def execute(
        self,
        kernel: GeometryKernel,
        geometry: StackGeometry2D | None,
        step: ProcessStep,
    ) -> OperationResult:
        """Deposit a blanket film over the current topography."""

        return OperationResult(
            kernel.deposit_blanket(_required(geometry), str(step.material_id), _thickness(step))
        )


class PatternedDepositOperation:
    """Patterned or inverted patterned deposition."""

    def execute(
        self,
        kernel: GeometryKernel,
        geometry: StackGeometry2D | None,
        step: ProcessStep,
    ) -> OperationResult:
        """Deposit material according to the step mask polarity."""

        return OperationResult(
            kernel.deposit_patterned(
                _required(geometry),
                str(step.material_id),
                _thickness(step),
                step.mask_intervals,
                step.mask_polarity,
            )
        )


class ConformalDepositOperation:
    """Exposed-surface conformal deposition executor."""

    def execute(
        self,
        kernel: GeometryKernel,
        geometry: StackGeometry2D | None,
        step: ProcessStep,
    ) -> OperationResult:
        """Grow material from exposed surfaces and emit approximation diagnostics."""

        source = _required(geometry)
        thickness = _thickness(step)
        profile = _conformal_profile(step)
        diagnostics = [_diag("warning", "CONFORMAL_APPROXIMATION_USED", step.id)]
        if profile.sidewall_coverage != 1.0:
            diagnostics.append(_diag("info", "CONFORMAL_SIDEWALL_COVERAGE_APPLIED", step.id))
        if profile.bottom_coverage != 1.0:
            diagnostics.append(_diag("info", "CONFORMAL_BOTTOM_COVERAGE_APPLIED", step.id))
        if _pinch_off_possible(source, step.mask_intervals, thickness, profile):
            diagnostics.append(_diag("warning", "CONFORMAL_PINCH_OFF", step.id))
            diagnostics.append(_diag("warning", "CONFORMAL_PINCH_OFF_APPROXIMATED", step.id))
            diagnostics.append(_diag("warning", "CONFORMAL_PINCH_OFF_DETECTED", step.id))
            diagnostics.append(_diag("warning", "CONFORMAL_VOID_OR_SEAM_DETECTED", step.id))
        diagnostics.append(_diag("info", "CONFORMAL_GEOMETRY_SIMPLIFIED", step.id))
        return OperationResult(
            kernel.deposit_conformal(
                source,
                str(step.material_id),
                thickness,
                profile,
                step.id,
                step.mask_intervals,
            ),
            tuple(diagnostics),
        )


class PlanarizeOperation:
    """Ideal planarization executor."""

    def execute(
        self,
        kernel: GeometryKernel,
        geometry: StackGeometry2D | None,
        step: ProcessStep,
    ) -> OperationResult:
        """Planarize stacks to the requested target height."""

        return OperationResult(kernel.planarize(_required(geometry), _planar_profile(step)))


class CMPPlanarizeOperation:
    """CMP heuristic planarization executor."""

    def execute(
        self,
        kernel: GeometryKernel,
        geometry: StackGeometry2D | None,
        step: ProcessStep,
    ) -> OperationResult:
        """Planarize with explicit CMP heuristic controls."""

        return OperationResult(
            kernel.cmp_planarize(_required(geometry), _planar_profile(step)),
            _legacy_and_contract_diagnostics(
                "warning", step.id, "CMP_HEURISTIC_USED", "CMP_DISHING_HEURISTIC_USED"
            ),
        )


class AnnotationOnlyOperation:
    """Operation that records metadata without geometry mutation."""

    def execute(
        self,
        kernel: GeometryKernel,
        geometry: StackGeometry2D | None,
        step: ProcessStep,
    ) -> OperationResult:
        """Leave geometry unchanged for annotation-only process steps."""
        return OperationResult(_required(geometry))
