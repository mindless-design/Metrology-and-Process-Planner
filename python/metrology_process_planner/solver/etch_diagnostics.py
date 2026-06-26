"""Etch operation diagnostics for sampled process geometry."""

from __future__ import annotations

from metrology_process_planner.solver.geometry_models import StackColumn, StackGeometry2D
from metrology_process_planner.solver.solver_outputs import SolverDiagnostic
from metrology_process_planner.solver.solver_profiles import EtchProfile


def etch_depth_diagnostics(
    geometry: StackGeometry2D,
    profile: EtchProfile,
    step_id: str,
    depth: float,
) -> tuple[SolverDiagnostic, ...]:
    """Return step-level warnings for etch blockers and exhausted target material."""

    summaries = tuple(_column_summary(column, profile, depth) for column in geometry.columns)
    diagnostics: list[SolverDiagnostic] = []
    blocked = [summary.blocker_material for summary in summaries if summary.blocker_material]
    exhausted = [summary for summary in summaries if summary.target_removed < depth]
    if blocked:
        diagnostics.append(
            _diagnostic(
                "ETCH_BLOCKED_BY_NON_TARGET",
                step_id,
                "Etch stopped on non-target material before reaching requested depth.",
                "blocked_materials=" + ",".join(sorted(set(blocked))),
            )
        )
    if exhausted:
        max_removed = max((summary.target_removed for summary in summaries), default=0.0)
        diagnostics.append(
            _diagnostic(
                "ETCH_TARGET_EXHAUSTED",
                step_id,
                "Requested etch depth exceeds available target material in sampled columns.",
                f"requested_depth={depth}; max_target_removed={max_removed}",
            )
        )
    return tuple(diagnostics)


class _ColumnEtchSummary:
    def __init__(self, target_removed: float, blocker_material: str) -> None:
        self.target_removed = target_removed
        self.blocker_material = blocker_material


def _column_summary(
    column: StackColumn,
    profile: EtchProfile,
    depth: float,
) -> _ColumnEtchSummary:
    remaining = depth
    target_removed = 0.0
    blocker = ""
    for interval in reversed(column.intervals):
        if remaining <= 0:
            break
        if interval.material_id in profile.stop_materials:
            break
        if profile.targets and interval.material_id not in profile.targets:
            blocker = interval.material_id
            break
        removed = min(remaining, interval.z_max - interval.z_min)
        target_removed += removed
        remaining -= removed
    return _ColumnEtchSummary(target_removed, blocker)


def _diagnostic(
    code: str,
    step_id: str,
    message: str,
    technical_details: str,
) -> SolverDiagnostic:
    return SolverDiagnostic(
        "warning",
        code,
        step_id,
        message,
        technical_details,
        output_usable=True,
    )
