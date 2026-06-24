"""Geometry-first v1 process solver orchestration."""

from __future__ import annotations

from typing import Callable

from metrology_process_planner.domains.process.geometry_kernel import GeometryKernel
from metrology_process_planner.domains.process.geometry_models import (
    CrossSectionProfile,
    CutlineSample,
    GeometrySnapshot,
    PointSample,
    StackGeometry2D,
)
from metrology_process_planner.domains.process.hybrid_diagnostics import (
    _hidden_material_diagnostics,
    _resolution_diagnostic,
    _step_resolution_diagnostics,
)
from metrology_process_planner.domains.process.operations import (
    AnnotationOnlyOperation,
    BlanketDepositOperation,
    CMPPlanarizeOperation,
    ConformalDepositOperation,
    DirectionalEtchOperation,
    IsotropicEtchOperation,
    OperationResult,
    PatternedDepositOperation,
    PlanarizeOperation,
    ProcessOperation,
    SubstrateOperation,
    TaperedEtchOperation,
)
from metrology_process_planner.domains.process.sampled_geometry_kernel import SampledGeometryKernel
from metrology_process_planner.domains.process.solver_outputs import (
    ProcessFrame,
    SolverDiagnostic,
    SolverInput,
    SolverResult,
)
from metrology_process_planner.domains.process.solver_profiles import SolverOptions
from metrology_process_planner.domains.process.steps import ProcessStep, ProcessStepKind

KernelFactory = Callable[[SolverOptions], GeometryKernel]


class HybridCrossSectionSolver:
    """Serious geometry-first communication solver for process planning."""

    def __init__(self, kernel_factory: KernelFactory | None = None) -> None:
        self._kernel_factory = kernel_factory or _sampled_kernel
        self._operations = _operation_map()

    def solve(self, solver_input: SolverInput, variant_label: str = "target") -> SolverResult:
        """Execute one target recipe variant and return render-ready outputs."""

        kernel = self._kernel_factory(solver_input.options)
        state = _RunState(variant_label)
        diagnostics = [_resolution_diagnostic(solver_input.options)]
        geometry: StackGeometry2D | None = None
        for step in solver_input.recipe.steps:
            diagnostics.extend(_step_resolution_diagnostics(step, solver_input.options))
            result = self._execute_step(kernel, geometry, step)
            geometry = result.geometry
            diagnostics.extend(result.diagnostics)
            diagnostics.extend(_hidden_material_diagnostics(solver_input.recipe, geometry, step))
            state.capture(kernel, geometry, step, solver_input.options)
        return _result_from_state(state, kernel, geometry, tuple(diagnostics), solver_input.options)

    def solve_variants(self, solver_input: SolverInput) -> tuple[SolverResult, ...]:
        """Execute recipe process-window variants with preserved labels."""

        windows = solver_input.recipe.process_windows
        if not windows:
            return (self.solve(solver_input),)
        labels: list[str] = []
        for window in windows:
            labels.extend((f"{window.name}:lower", f"{window.name}:target", f"{window.name}:upper"))
        return tuple(self.solve(solver_input, label) for label in labels)

    def _execute_step(
        self,
        kernel: GeometryKernel,
        geometry: StackGeometry2D | None,
        step: ProcessStep,
    ) -> OperationResult:
        operation = self._operations.get(step.kind)
        if operation is None:
            raise ValueError(f"Unsupported process step kind: {step.kind.value}")
        return operation.execute(kernel, geometry, step)


class _RunState:
    def __init__(self, variant_label: str) -> None:
        self.variant_label = variant_label
        self.frames: list[ProcessFrame] = []
        self.snapshots: list[GeometrySnapshot] = []

    def capture(
        self,
        kernel: GeometryKernel,
        geometry: StackGeometry2D,
        step: ProcessStep,
        options: SolverOptions,
    ) -> None:
        if options.frame_every_step:
            self.frames.append(_frame(kernel, geometry, step, self.variant_label))
        self.snapshots.append(_snapshot(kernel, geometry, step))


def _sampled_kernel(options: SolverOptions) -> GeometryKernel:
    return SampledGeometryKernel(options.x_min, options.x_max, options.sample_count)


def _operation_map() -> dict[ProcessStepKind, ProcessOperation]:
    conformal = ConformalDepositOperation()
    return {
        ProcessStepKind.SUBSTRATE: SubstrateOperation(),
        ProcessStepKind.BLANKET_DEPOSITION: BlanketDepositOperation(),
        ProcessStepKind.PATTERNED_DEPOSITION: PatternedDepositOperation(),
        ProcessStepKind.CONFORMAL_COATING: conformal,
        ProcessStepKind.CONFORMAL_DEPOSITION: conformal,
        ProcessStepKind.DIRECTIONAL_ETCH: DirectionalEtchOperation(),
        ProcessStepKind.ISOTROPIC_ETCH: IsotropicEtchOperation(),
        ProcessStepKind.TAPERED_ETCH: TaperedEtchOperation(),
        ProcessStepKind.PLANARIZATION: PlanarizeOperation(),
        ProcessStepKind.CMP_PLANARIZATION: CMPPlanarizeOperation(),
        ProcessStepKind.ANNOTATION_ONLY: AnnotationOnlyOperation(),
    }


def _frame(
    kernel: GeometryKernel,
    geometry: StackGeometry2D,
    step: ProcessStep,
    label: str,
) -> ProcessFrame:
    return ProcessFrame(
        step.id,
        step.notes or step.id,
        CrossSectionProfile(geometry.columns),
        kernel.make_render_projection(geometry),
        {"variant_label": label, "step_kind": step.kind.value},
    )


def _snapshot(
    kernel: GeometryKernel,
    geometry: StackGeometry2D,
    step: ProcessStep,
) -> GeometrySnapshot:
    return GeometrySnapshot(
        step.id,
        geometry,
        kernel.compute_signature(geometry),
        {"kind": step.kind.value},
    )


def _result_from_state(
    state: _RunState,
    kernel: GeometryKernel,
    geometry: StackGeometry2D | None,
    diagnostics: tuple[SolverDiagnostic, ...],
    options: SolverOptions,
) -> SolverResult:
    point_samples: tuple[PointSample, ...] = ()
    cutline_samples: tuple[CutlineSample, ...] = ()
    if geometry is not None:
        point_samples = tuple(
            kernel.extract_point_stack(geometry, x) for x in options.point_sample_xs
        )
        cutline_samples = _extract_cutline(kernel, geometry, options)
    return SolverResult(
        tuple(state.frames),
        diagnostics,
        point_samples,
        cutline_samples,
        tuple(state.snapshots),
        state.variant_label,
    )


def _extract_cutline(
    kernel: GeometryKernel,
    geometry: StackGeometry2D,
    options: SolverOptions,
) -> tuple[CutlineSample, ...]:
    if options.cutline_x_min is None or options.cutline_x_max is None:
        return ()
    return kernel.extract_cutline_profile(geometry, options.cutline_x_min, options.cutline_x_max)
