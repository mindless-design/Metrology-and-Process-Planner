"""Input and recipe validation for deterministic solver execution."""

from __future__ import annotations

from metrology_process_planner.domains.process.recipe import ProcessRecipe
from metrology_process_planner.domains.process.steps import ProcessStep, ProcessStepKind
from metrology_process_planner.solver.solver_outputs import SolverDiagnostic, SolverInput

SUPPORTED_BACKENDS = ("sampled_geometry",)


def validate_solver_input(solver_input: SolverInput | None) -> tuple[SolverDiagnostic, ...]:
    """Return structured diagnostics for invalid solver inputs."""

    if solver_input is None:
        return (_diagnostic("error", "MISSING_RECIPE", "", "Solver input is missing.", False),)
    diagnostics: list[SolverDiagnostic] = []
    recipe = solver_input.recipe
    if recipe is None:
        diagnostics.append(_diagnostic("error", "MISSING_RECIPE", "", "Recipe is missing.", False))
        return tuple(diagnostics)
    diagnostics.extend(_validate_backend(solver_input.backend_id))
    diagnostics.extend(_validate_units(solver_input.units, recipe))
    diagnostics.extend(_validate_recipe(recipe))
    return tuple(diagnostics)


def _validate_backend(backend_id: str) -> tuple[SolverDiagnostic, ...]:
    if backend_id in SUPPORTED_BACKENDS:
        return ()
    return (
        _diagnostic(
            "error",
            "UNSUPPORTED_SOLVER_BACKEND",
            "",
            f"Unsupported solver backend: {backend_id}.",
            False,
        ),
    )


def _validate_units(units: str, recipe: ProcessRecipe) -> tuple[SolverDiagnostic, ...]:
    diagnostics: list[SolverDiagnostic] = []
    if not units:
        diagnostics.append(
            _diagnostic("error", "INCONSISTENT_UNITS", "", "Solver units are missing.", False)
        )
    for step in recipe.steps:
        if step.thickness is not None and step.thickness.unit != units:
            diagnostics.append(
                _diagnostic(
                    "error",
                    "INCONSISTENT_UNITS",
                    step.id,
                    f"Step {step.id} thickness unit {step.thickness.unit} does not match {units}.",
                    False,
                    step.notes,
                )
            )
    return tuple(diagnostics)


def _validate_recipe(recipe: ProcessRecipe) -> tuple[SolverDiagnostic, ...]:
    material_ids = {material.id for material in recipe.materials}
    diagnostics: list[SolverDiagnostic] = []
    if not recipe.steps:
        diagnostics.append(
            _diagnostic("error", "MISSING_RECIPE", "", "Recipe has no steps.", False)
        )
    for warning in recipe.validate():
        code = _code_from_warning(warning)
        usable = _warning_output_usable(code, warning)
        severity = "warning" if usable else "error"
        diagnostics.append(
            _diagnostic(severity, code, _step_id_from_warning(warning), warning, usable)
        )
    for window in recipe.process_windows:
        if window.lower > window.target or window.target > window.upper:
            diagnostics.append(
                _diagnostic(
                    "error",
                    "INVALID_PROCESS_WINDOW",
                    "",
                    f"Process window {window.name} must satisfy lower <= target <= upper.",
                    False,
                )
            )
    for step in recipe.steps:
        diagnostics.extend(_validate_step_shape(step, material_ids))
    return tuple(diagnostics)


def _validate_step_shape(
    step: ProcessStep,
    material_ids: set[str],
) -> tuple[SolverDiagnostic, ...]:
    diagnostics: list[SolverDiagnostic] = []
    if step.kind not in set(ProcessStepKind):
        diagnostics.append(
            _diagnostic(
                "error",
                "UNSUPPORTED_OPERATION",
                step.id,
                "Unsupported operation type.",
                False,
            )
        )
    if (step.parameters or {}).get("enabled") is False:
        diagnostics.append(_diagnostic("info", "STEP_DISABLED", step.id, "Step is disabled.", True))
    if step.thickness is not None and step.thickness.target < 0:
        diagnostics.append(
            _diagnostic(
                "error",
                "INVALID_THICKNESS",
                step.id,
                "Thickness must be non-negative.",
                False,
            )
        )
    for interval in step.mask_intervals:
        if interval.x_max <= interval.x_min:
            diagnostics.append(
                _diagnostic("error", "EMPTY_MASK", step.id, "Mask interval has no width.", False)
            )
    if step.material_id is not None and step.material_id not in material_ids:
        diagnostics.append(
            _diagnostic(
                "error",
                "MISSING_LAYER",
                step.id,
                "Step material is not resolvable.",
                False,
            )
        )
    return tuple(diagnostics)


def _code_from_warning(warning: str) -> str:
    if "requires a layer reference" in warning:
        return "MISSING_LAYER"
    if "thickness" in warning.lower():
        return "INVALID_THICKNESS"
    if "process window" in warning.lower() or "Window " in warning:
        return "INVALID_PROCESS_WINDOW"
    if "unknown material" in warning:
        return "MISSING_LAYER"
    return "INVALID_RECIPE_INPUT"


def _step_id_from_warning(warning: str) -> str:
    parts = warning.split()
    if len(parts) >= 2 and parts[0] == "Step":
        return parts[1].rstrip(":")
    return ""


def _warning_output_usable(code: str, warning: str) -> bool:
    if code == "MISSING_LAYER" and "requires a layer reference" in warning:
        return True
    return code not in {"INVALID_THICKNESS", "INVALID_PROCESS_WINDOW", "MISSING_RECIPE"}


def _diagnostic(
    severity: str,
    code: str,
    step_id: str,
    message: str,
    usable: bool,
    step_name: str = "",
) -> SolverDiagnostic:
    return SolverDiagnostic(
        severity,
        code,
        step_id,
        message,
        suggested_repair="Fix the recipe or solver request before rendering.",
        output_usable=usable,
        step_name=step_name,
    )
