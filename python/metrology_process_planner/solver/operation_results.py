"""Shared result model for process operation executors."""

from __future__ import annotations

from dataclasses import dataclass

from metrology_process_planner.solver.geometry_models import StackGeometry2D
from metrology_process_planner.solver.solver_outputs import SolverDiagnostic


@dataclass(frozen=True)
class OperationResult:
    """Result from executing one process operation."""

    geometry: StackGeometry2D
    diagnostics: tuple[SolverDiagnostic, ...] = ()
