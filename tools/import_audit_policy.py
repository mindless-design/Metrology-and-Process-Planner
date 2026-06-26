"""Deprecated import paths and compatibility-shim inventory for audit tools."""

from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PACKAGE_ROOT = ROOT / "python" / "metrology_process_planner"

SESSION_REPLACEMENTS = {
    "artifact_content": "metrology_process_planner.domains.artifacts.artifact_content",
    "artifact_ids": "metrology_process_planner.domains.artifacts.artifact_ids",
    "artifact_query": "metrology_process_planner.domains.artifacts.artifact_query",
    "artifact_refs_metadata": (
        "metrology_process_planner.domains.artifacts.artifact_refs_metadata"
    ),
    "artifact_registry": "metrology_process_planner.domains.artifacts.artifact_registry",
    "artifact_repair_metadata": (
        "metrology_process_planner.domains.artifacts.artifact_repair_metadata"
    ),
    "artifact_visibility": "metrology_process_planner.domains.artifacts.artifact_visibility",
    "canvas": "metrology_process_planner.domains.capture.canvas",
    "capture_features": "metrology_process_planner.domains.capture.capture_features",
    "capture_geometry": "metrology_process_planner.domains.capture.capture_geometry",
    "capture_geometry_validation": (
        "metrology_process_planner.domains.capture.capture_geometry_validation"
    ),
    "captures": "metrology_process_planner.domains.capture.captures",
    "grids": "metrology_process_planner.domains.capture.grids",
    "legacy_artifacts": "metrology_process_planner.domains.artifacts.legacy_artifacts",
    "mode_builtins": "metrology_process_planner.domains.modes.mode_builtins",
    "mode_definition_io": "metrology_process_planner.domains.modes.mode_definition_io",
    "mode_execution": "metrology_process_planner.domains.modes.mode_execution",
    "mode_fallback": "metrology_process_planner.domains.modes.mode_fallback",
    "mode_grid_builtin": "metrology_process_planner.domains.modes.mode_grid_builtin",
    "mode_loader": "metrology_process_planner.domains.modes.mode_loader",
    "mode_non_process_builtins": (
        "metrology_process_planner.domains.modes.mode_non_process_builtins"
    ),
    "mode_non_process_support": (
        "metrology_process_planner.domains.modes.mode_non_process_support"
    ),
    "mode_non_process_validation": (
        "metrology_process_planner.domains.modes.mode_non_process_validation"
    ),
    "mode_output_policies": "metrology_process_planner.domains.modes.mode_output_policies",
    "mode_policies": "metrology_process_planner.domains.modes.mode_policies",
    "mode_process_constants": (
        "metrology_process_planner.domains.modes.mode_process_constants"
    ),
    "mode_process_flow": "metrology_process_planner.domains.modes.mode_process_flow",
    "mode_registry": "metrology_process_planner.domains.modes.mode_registry",
    "mode_validation": "metrology_process_planner.domains.modes.mode_validation",
    "warning_visibility": "metrology_process_planner.domains.warnings.warning_visibility",
    "warnings": "metrology_process_planner.domains.warnings.warnings",
}

SOLVER_SHIMS = (
    "etch_diagnostics",
    "etch_operations",
    "geometry_kernel",
    "geometry_models",
    "hybrid_diagnostics",
    "hybrid_solver",
    "invariants",
    "operation_helpers",
    "operation_results",
    "operations",
    "pyxs_compat",
    "sampled_geometry_helpers",
    "sampled_geometry_kernel",
    "solver_models",
    "solver_outputs",
    "solver_profiles",
    "solver_projection_builders",
    "solver_result_builders",
    "solver_result_support",
    "solver_validation",
)

DIAGNOSTICS_SHIMS = (
    "diagnostics",
    "diagnostics_assertions",
    "diagnostics_bundle",
    "diagnostics_diffs",
    "diagnostics_exceptions",
    "diagnostics_models",
    "diagnostics_project",
    "diagnostics_seams",
    "diagnostics_sinks",
    "diagnostics_snapshots",
    "diagnostics_timeline",
)

DEPRECATED_IMPORTS = {
    "metrology_process_planner.domains.measurements": (
        "metrology_process_planner.domains.measurement.records"
    ),
    **{
        f"metrology_process_planner.domains.session.{name}": replacement
        for name, replacement in SESSION_REPLACEMENTS.items()
    },
    **{
        f"metrology_process_planner.domains.process.{name}": (
            f"metrology_process_planner.solver.{name}"
        )
        for name in SOLVER_SHIMS
    },
    **{
        f"metrology_process_planner.infrastructure.{name}": (
            f"metrology_process_planner.diagnostics.{name}"
        )
        for name in DIAGNOSTICS_SHIMS
    },
    "metrology_process_planner.infrastructure.trace_context": (
        "metrology_process_planner.diagnostics.trace_context"
    ),
}

APPROVED_PYA_ROOTS = (
    PACKAGE_ROOT / "infrastructure" / "klayout",
    ROOT / "pymacros",
)


def deprecated_shim_paths() -> tuple[Path, ...]:
    """Return removed compatibility shim file paths that must not reappear."""

    domain_session = tuple(
        PACKAGE_ROOT / "domains" / "session" / f"{name}.py"
        for name in SESSION_REPLACEMENTS
    )
    solver = tuple(
        PACKAGE_ROOT / "domains" / "process" / f"{name}.py" for name in SOLVER_SHIMS
    )
    diagnostics = tuple(
        PACKAGE_ROOT / "infrastructure" / f"{name}.py" for name in DIAGNOSTICS_SHIMS
    )
    return (
        PACKAGE_ROOT / "domains" / "measurements.py",
        *domain_session,
        *solver,
        *diagnostics,
        PACKAGE_ROOT / "infrastructure" / "trace_context.py",
    )
