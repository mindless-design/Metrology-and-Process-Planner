"""Frame capture and result assembly helpers for the hybrid solver."""

from __future__ import annotations

from metrology_process_planner.domains.process.steps import ProcessStep
from metrology_process_planner.solver.geometry_kernel import GeometryKernel
from metrology_process_planner.solver.geometry_models import (
    CrossSectionProfile,
    CutlineSample,
    GeometrySnapshot,
    PointSample,
    RenderProjection,
    StackGeometry2D,
)
from metrology_process_planner.solver.solver_outputs import (
    ProcessFrame,
    SolverDiagnostic,
    SolverInput,
    SolverResult,
)
from metrology_process_planner.solver.solver_profiles import SolverOptions
from metrology_process_planner.solver.solver_projection_builders import (
    projection_from_geometry,
)
from metrology_process_planner.solver.solver_result_support import (
    input_hash,
    material_metadata,
    metrics,
    strict_projection_diagnostics,
)


class RunState:
    """Mutable state captured while one solver variant executes."""

    def __init__(self, variant_label: str) -> None:
        self.variant_label = variant_label
        self.frames: list[ProcessFrame] = []
        self.snapshots: list[GeometrySnapshot] = []
        self._previous_signature = ""

    def capture(
        self,
        kernel: GeometryKernel,
        geometry: StackGeometry2D,
        step: ProcessStep,
        step_index: int,
        options: SolverOptions,
        diagnostics: tuple[SolverDiagnostic, ...],
    ) -> None:
        """Capture a process frame and snapshot after one step."""

        signature = kernel.compute_signature(geometry)
        changed = signature != self._previous_signature
        if options.frame_every_step:
            self.frames.append(
                _frame(kernel, geometry, step, step_index, self.variant_label, signature,
                       changed, diagnostics)
            )
        self.snapshots.append(_snapshot(geometry, step, signature))
        self._previous_signature = signature


def result_from_state(
    state: RunState,
    kernel: GeometryKernel,
    geometry: StackGeometry2D | None,
    diagnostics: tuple[SolverDiagnostic, ...],
    solver_input: SolverInput,
) -> SolverResult:
    """Build the public solver result from captured state."""

    point_samples: tuple[PointSample, ...] = ()
    cutline_samples: tuple[CutlineSample, ...] = ()
    projection: tuple[RenderProjection, ...] = ()
    if geometry is not None:
        point_samples = tuple(
            kernel.extract_point_stack(geometry, x) for x in solver_input.options.point_sample_xs
        )
        cutline_samples = _extract_cutline(kernel, geometry, solver_input.options)
        projection = (
            projection_from_geometry(
                kernel,
                geometry,
                None,
                state.variant_label,
                diagnostics,
                solver_input,
            ),
        )
    if solver_input.options.strict_mode:
        diagnostics = (*diagnostics, *strict_projection_diagnostics(projection))
    return SolverResult(
        tuple(state.frames),
        diagnostics,
        point_samples,
        cutline_samples,
        tuple(state.snapshots),
        state.variant_label,
        input_hash=input_hash(solver_input),
        recipe_id=solver_input.recipe.id,
        final_stack=geometry,
        render_projections=projection,
        approximation_notes=tuple(item.message for item in diagnostics if "APPROXIM" in item.code),
        metrics=metrics(geometry, state.frames),
        units=solver_input.units,
        material_metadata=material_metadata(solver_input),
    )


def empty_result(
    solver_input: SolverInput | None,
    variant_label: str,
    diagnostics: tuple[SolverDiagnostic, ...],
) -> SolverResult:
    """Build an empty result for validation failures."""

    recipe_id = solver_input.recipe.id if solver_input is not None and solver_input.recipe else ""
    units = solver_input.units if solver_input is not None else "um"
    return SolverResult(
        (),
        diagnostics,
        variant_label=variant_label,
        recipe_id=recipe_id,
        units=units,
        metrics={"column_count": 0, "frame_count": 0},
    )


def has_blocking(diagnostics: list[SolverDiagnostic]) -> bool:
    """Return whether diagnostics contain a blocking error."""

    return any(not item.output_usable for item in diagnostics if item.severity == "error")


def step_diag(severity: str, code: str, step: ProcessStep) -> SolverDiagnostic:
    """Build a step-scoped solver diagnostic."""

    return SolverDiagnostic(
        severity,
        code,
        step.id,
        code.replace("_", " ").title(),
        step_name=step.notes or step.id,
        output_usable=severity != "error",
    )


def _frame(
    kernel: GeometryKernel,
    geometry: StackGeometry2D,
    step: ProcessStep,
    step_index: int,
    label: str,
    signature: str,
    changed: bool,
    diagnostics: tuple[SolverDiagnostic, ...],
) -> ProcessFrame:
    projection = projection_from_geometry(kernel, geometry, step, label, diagnostics)
    return ProcessFrame(
        step.id, step.notes or step.id, CrossSectionProfile(geometry.columns), projection,
        {"variant_label": label, "step_kind": step.kind.value},
        f"frame:{label}:{step_index}:{step.id}", step_index, step.notes or step.id,
        step.kind.value, signature, changed, projection.changed_regions, diagnostics, label,
        projection,
    )


def _snapshot(geometry: StackGeometry2D, step: ProcessStep, signature: str) -> GeometrySnapshot:
    return GeometrySnapshot(step.id, geometry, signature, {"kind": step.kind.value})


def _extract_cutline(
    kernel: GeometryKernel,
    geometry: StackGeometry2D,
    options: SolverOptions,
) -> tuple[CutlineSample, ...]:
    if options.cutline_x_min is None or options.cutline_x_max is None:
        return ()
    return kernel.extract_cutline_profile(geometry, options.cutline_x_min, options.cutline_x_max)
