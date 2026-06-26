"""Process solver package with stable public re-exports."""

from __future__ import annotations

from importlib import import_module
from typing import Any

_EXPORTS = {
    "ApproximationPolicy": "metrology_process_planner.solver.solver_models",
    "AdvancedGeometryKernel": "metrology_process_planner.solver.advanced_geometry_kernel",
    "ConformalLayerMetadata": "metrology_process_planner.solver.solver_models",
    "ConformalProfile": "metrology_process_planner.solver.solver_models",
    "CrossSectionProfile": "metrology_process_planner.solver.solver_models",
    "CutlineSample": "metrology_process_planner.solver.solver_models",
    "EtchProfile": "metrology_process_planner.solver.solver_models",
    "GeometryKernel": "metrology_process_planner.solver.geometry_kernel",
    "GeometrySnapshot": "metrology_process_planner.solver.solver_models",
    "HybridCrossSectionSolver": "metrology_process_planner.solver.hybrid_solver",
    "MaskInterval": "metrology_process_planner.solver.solver_models",
    "MaterialInterval": "metrology_process_planner.solver.solver_models",
    "MaterialRegion": "metrology_process_planner.solver.solver_models",
    "PlanarizationProfile": "metrology_process_planner.solver.solver_models",
    "PointSample": "metrology_process_planner.solver.solver_models",
    "PinchOffRegion": "metrology_process_planner.solver.solver_models",
    "ProcessFrame": "metrology_process_planner.solver.solver_models",
    "ProcessProfile": "metrology_process_planner.solver.solver_models",
    "PyxsComparisonRequest": "metrology_process_planner.solver.solver_models",
    "RecipeToPyxsPlan": "metrology_process_planner.solver.solver_models",
    "RenderProjection": "metrology_process_planner.solver.solver_models",
    "SampledGeometryKernel": "metrology_process_planner.solver.sampled_geometry_kernel",
    "SolverDiagnostic": "metrology_process_planner.solver.solver_models",
    "SolverInput": "metrology_process_planner.solver.solver_models",
    "SolverOptions": "metrology_process_planner.solver.solver_models",
    "SolverResult": "metrology_process_planner.solver.solver_models",
    "StackColumn": "metrology_process_planner.solver.solver_models",
    "StackGeometry2D": "metrology_process_planner.solver.solver_models",
    "StackInvariantChecker": "metrology_process_planner.solver.solver_models",
    "SurfaceProfile": "metrology_process_planner.solver.solver_models",
    "TaperedRegion": "metrology_process_planner.solver.solver_models",
    "UndercutRegion": "metrology_process_planner.solver.solver_models",
    "VoidRegion": "metrology_process_planner.solver.solver_models",
    "build_recipe_to_pyxs_plan": "metrology_process_planner.solver.pyxs_compat",
    "validate_render_projection": "metrology_process_planner.solver.solver_models",
    "validate_solver_input": "metrology_process_planner.solver.solver_models",
}

__all__ = list(_EXPORTS)


def __getattr__(name: str) -> Any:
    """Load public solver exports on first access."""

    module_name = _EXPORTS.get(name)
    if module_name is None:
        raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
    value = getattr(import_module(module_name), name)
    globals()[name] = value
    return value
