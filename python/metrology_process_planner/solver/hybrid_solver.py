"""Geometry-first process solver orchestration."""

from __future__ import annotations

from typing import Callable

from metrology_process_planner.domains.process.steps import ProcessStep, ProcessStepKind
from metrology_process_planner.solver.advanced_geometry_kernel import AdvancedGeometryKernel
from metrology_process_planner.solver.etch_operations import (
    DirectionalEtchOperation,
    IsotropicEtchOperation,
    TaperedEtchOperation,
)
from metrology_process_planner.solver.geometry_kernel import GeometryKernel
from metrology_process_planner.solver.geometry_models import StackGeometry2D
from metrology_process_planner.solver.hybrid_diagnostics import (
    _hidden_material_diagnostics,
    _resolution_diagnostic,
    _step_resolution_diagnostics,
)
from metrology_process_planner.solver.invariants import StackInvariantChecker
from metrology_process_planner.solver.operation_results import OperationResult
from metrology_process_planner.solver.operations import (
    AnnotationOnlyOperation,
    BlanketDepositOperation,
    CMPPlanarizeOperation,
    ConformalDepositOperation,
    PatternedDepositOperation,
    PlanarizeOperation,
    ProcessOperation,
    SubstrateOperation,
)
from metrology_process_planner.solver.solver_outputs import (
    SolverDiagnostic,
    SolverInput,
    SolverResult,
)
from metrology_process_planner.solver.solver_profiles import SolverOptions
from metrology_process_planner.solver.solver_result_builders import (
    RunState,
    empty_result,
    has_blocking,
    result_from_state,
    step_diag,
)
from metrology_process_planner.solver.solver_validation import validate_solver_input

KernelFactory = Callable[[SolverOptions], GeometryKernel]


class HybridCrossSectionSolver:
    """Execute process recipes with a sampled geometry kernel."""

    def __init__(self, kernel_factory: KernelFactory | None = None) -> None:
        self._kernel_factory = kernel_factory or _sampled_kernel
        self._operations = _operation_map()

    def solve(self, solver_input: SolverInput, variant_label: str = "target") -> SolverResult:
        """Execute one target recipe variant and return render-ready outputs."""

        input_diagnostics = list(validate_solver_input(solver_input))
        if has_blocking(input_diagnostics):
            return empty_result(solver_input, variant_label, tuple(input_diagnostics))
        kernel = self._kernel_factory(solver_input.options)
        state = RunState(variant_label)
        diagnostics: list[SolverDiagnostic] = [_resolution_diagnostic(solver_input.options)]
        diagnostics.extend(input_diagnostics)
        checker = StackInvariantChecker({material.id for material in solver_input.recipe.materials})
        geometry: StackGeometry2D | None = None
        for step_index, step in enumerate(solver_input.recipe.steps):
            if (step.parameters or {}).get("enabled") is False:
                diagnostics.append(step_diag("info", "STEP_DISABLED", step))
                continue
            step_diagnostics = list(_step_resolution_diagnostics(step, solver_input.options))
            result = self._execute_step(kernel, geometry, step)
            geometry = result.geometry
            step_diagnostics.extend(result.diagnostics)
            step_diagnostics.extend(
                _hidden_material_diagnostics(solver_input.recipe, geometry, step)
            )
            if solver_input.options.strict_mode:
                step_diagnostics.extend(checker.check_stack_model(geometry, step.id).diagnostics)
            diagnostics.extend(step_diagnostics)
            state.capture(
                kernel,
                geometry,
                step,
                step_index,
                solver_input.options,
                tuple(step_diagnostics),
            )
        if solver_input.options.strict_mode:
            diagnostics.extend(checker.check_process_frames(tuple(state.frames)).diagnostics)
        return result_from_state(state, kernel, geometry, tuple(diagnostics), solver_input)

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
            fallback = geometry or kernel.initialize_substrate("__invalid__", 0.0)
            return OperationResult(fallback, (step_diag("error", "UNSUPPORTED_OPERATION", step),))
        try:
            return operation.execute(kernel, geometry, step)
        except ValueError as error:
            fallback = geometry or kernel.initialize_substrate("__invalid__", 0.0)
            diagnostic = SolverDiagnostic(
                "error",
                "INVALID_RECIPE_INPUT",
                step.id,
                str(error),
                output_usable=False,
                step_name=step.notes or step.id,
            )
            return OperationResult(fallback, (diagnostic,))


def _sampled_kernel(options: SolverOptions) -> GeometryKernel:
    return AdvancedGeometryKernel(options.x_min, options.x_max, options.sample_count)


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
