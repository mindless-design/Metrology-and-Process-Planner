"""Diagnostic helpers for the hybrid process solver."""

from __future__ import annotations

from metrology_process_planner.domains.process.recipe import ProcessRecipe
from metrology_process_planner.domains.process.steps import ProcessStep
from metrology_process_planner.solver.geometry_models import StackGeometry2D
from metrology_process_planner.solver.solver_outputs import SolverDiagnostic
from metrology_process_planner.solver.solver_profiles import SolverOptions


def _resolution_diagnostic(options: SolverOptions) -> SolverDiagnostic:
    policy = options.approximation_policy
    return SolverDiagnostic(
        "info",
        "GEOMETRY_RESOLUTION",
        "solver",
        "Sampled-column geometry resolution is active.",
        f"samples={options.sample_count}; grid_resolution={policy.grid_resolution}",
    )


def _step_resolution_diagnostics(
    step: ProcessStep,
    options: SolverOptions,
) -> tuple[SolverDiagnostic, ...]:
    policy = options.approximation_policy
    if not policy.emit_resolution_diagnostics:
        return ()
    diagnostics: list[SolverDiagnostic] = []
    for interval in step.mask_intervals:
        if interval.width < policy.min_feature_width:
            diagnostics.append(_step_diag("warning", "FEATURE_BELOW_GRID_RESOLUTION", step.id))
    return tuple(diagnostics)


def _hidden_material_diagnostics(
    recipe: ProcessRecipe,
    geometry: StackGeometry2D,
    step: ProcessStep,
) -> tuple[SolverDiagnostic, ...]:
    hidden = {material.id for material in recipe.materials if not material.visible}
    if not hidden:
        return ()
    has_hidden_top = any(
        column.intervals and column.intervals[-1].material_id in hidden
        for column in geometry.columns
    )
    if not has_hidden_top:
        return ()
    return (_step_diag("warning", "HIDDEN_MATERIAL_AFFECTS_HEIGHT", step.id),)


def _step_diag(severity: str, code: str, step_id: str) -> SolverDiagnostic:
    return SolverDiagnostic(severity, code, step_id, code.replace("_", " ").title())
