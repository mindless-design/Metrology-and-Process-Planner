"""Modular operation executors for the hybrid cross-section solver."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol

from metrology_process_planner.domains.process.geometry_kernel import GeometryKernel
from metrology_process_planner.domains.process.geometry_models import StackGeometry2D
from metrology_process_planner.domains.process.operation_helpers import (
    _diag,
    _etch_profile,
    _pinch_off_possible,
    _planar_profile,
    _required,
    _thickness,
)
from metrology_process_planner.domains.process.solver_outputs import SolverDiagnostic
from metrology_process_planner.domains.process.solver_profiles import ConformalProfile
from metrology_process_planner.domains.process.steps import ProcessStep


@dataclass(frozen=True)
class OperationResult:
    """Result from executing one process operation."""

    geometry: StackGeometry2D
    diagnostics: tuple[SolverDiagnostic, ...] = ()


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
        profile = step.conformal_profile or ConformalProfile()
        diagnostics = [_diag("warning", "CONFORMAL_APPROXIMATION_USED", step.id)]
        if _pinch_off_possible(source, step.mask_intervals, thickness, profile):
            diagnostics.append(_diag("warning", "CONFORMAL_PINCH_OFF", step.id))
        return OperationResult(
            kernel.deposit_conformal(source, str(step.material_id), thickness, profile),
            tuple(diagnostics),
        )


class DirectionalEtchOperation:
    """Directional top-down etch executor."""

    def execute(
        self,
        kernel: GeometryKernel,
        geometry: StackGeometry2D | None,
        step: ProcessStep,
    ) -> OperationResult:
        """Etch target materials top-down until depth or blocker stops removal."""

        return OperationResult(kernel.etch_directional(_required(geometry), _etch_profile(step)))


class IsotropicEtchOperation:
    """Isotropic exposed-boundary etch executor."""

    def execute(
        self,
        kernel: GeometryKernel,
        geometry: StackGeometry2D | None,
        step: ProcessStep,
    ) -> OperationResult:
        """Etch target materials with lateral attack diagnostics."""

        profile = _etch_profile(step)
        return OperationResult(
            kernel.etch_isotropic(_required(geometry), profile),
            (_diag("warning", "ISOTROPIC_UNDERCUT", step.id),),
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

        return OperationResult(
            kernel.etch_tapered(_required(geometry), _etch_profile(step)),
            (_diag("info", "TAPERED_PROFILE_APPROXIMATION", step.id),),
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
            (_diag("warning", "CMP_HEURISTIC_USED", step.id),),
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
