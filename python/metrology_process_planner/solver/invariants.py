"""Stack and process-frame invariant checks for solver outputs."""

from __future__ import annotations

from dataclasses import dataclass

from metrology_process_planner.solver.geometry_models import (
    MaterialInterval,
    StackColumn,
    StackGeometry2D,
    SurfaceProfile,
)
from metrology_process_planner.solver.solver_outputs import ProcessFrame, SolverDiagnostic


@dataclass(frozen=True)
class InvariantCheckResult:
    """Structured result from stack invariant validation."""

    diagnostics: tuple[SolverDiagnostic, ...] = ()

    @property
    def passed(self) -> bool:
        """Return whether no invariant violation was found."""

        return not self.diagnostics


class StackInvariantChecker:
    """Validate stack geometry before renderer-facing use."""

    def __init__(self, material_ids: set[str] | None = None) -> None:
        self._material_ids = material_ids

    def check_stack_model(self, stack: StackGeometry2D, step_id: str = "") -> InvariantCheckResult:
        """Check all stack columns and surface consistency."""

        diagnostics: list[SolverDiagnostic] = []
        if not stack.columns:
            diagnostics.append(_violation(step_id, "Stack geometry has no columns."))
            return InvariantCheckResult(tuple(diagnostics))
        previous_x: float | None = None
        for column in stack.columns:
            diagnostics.extend(self.check_stack_column(column, step_id).diagnostics)
            if previous_x is not None and column.x <= previous_x:
                diagnostics.append(_violation(step_id, "Stack column x positions must increase."))
            previous_x = column.x
        diagnostics.extend(self.check_surface_profile(stack.surface, stack, step_id).diagnostics)
        return InvariantCheckResult(tuple(diagnostics))

    def check_stack_column(self, column: StackColumn, step_id: str = "") -> InvariantCheckResult:
        """Check x coordinate and material intervals in one column."""

        diagnostics: list[SolverDiagnostic] = []
        if not isinstance(column.x, (int, float)):
            diagnostics.append(_violation(step_id, "Stack column x coordinate is invalid."))
        diagnostics.extend(self.check_material_intervals(column.intervals, step_id).diagnostics)
        ordered = sorted(
            column.intervals,
            key=lambda item: (item.z_min, item.z_max, item.material_id),
        )
        for lower, upper in zip(ordered, ordered[1:]):
            if lower.z_max > upper.z_min:
                diagnostics.append(_violation(step_id, "Material intervals overlap in one column."))
        return InvariantCheckResult(tuple(diagnostics))

    def check_material_intervals(
        self,
        intervals: tuple[MaterialInterval, ...],
        step_id: str = "",
    ) -> InvariantCheckResult:
        """Check interval thickness and material references."""

        diagnostics: list[SolverDiagnostic] = []
        for interval in intervals:
            if interval.z_max <= interval.z_min:
                diagnostics.append(
                    _violation(step_id, "Material interval must satisfy z_max > z_min.")
                )
            if not interval.material_id:
                diagnostics.append(_violation(step_id, "Material interval has no material id."))
            if self._material_ids is not None and interval.material_id not in self._material_ids:
                diagnostics.append(
                    _violation(step_id, f"Unknown material id in stack: {interval.material_id}.")
                )
        return InvariantCheckResult(tuple(diagnostics))

    def check_surface_profile(
        self,
        surface: SurfaceProfile,
        stack: StackGeometry2D,
        step_id: str = "",
    ) -> InvariantCheckResult:
        """Check that surface profile points match column tops."""

        diagnostics: list[SolverDiagnostic] = []
        if len(surface.points) != len(stack.columns):
            diagnostics.append(_violation(step_id, "Surface point count must match stack columns."))
            return InvariantCheckResult(tuple(diagnostics))
        for point, column in zip(surface.points, stack.columns):
            x, z = point
            if x != column.x or z != column.top:
                diagnostics.append(_violation(step_id, "Surface profile must match column tops."))
                break
        return InvariantCheckResult(tuple(diagnostics))

    def check_process_frames(self, frames: tuple[ProcessFrame, ...]) -> InvariantCheckResult:
        """Check frame ordering, signatures, and embedded profiles."""

        diagnostics: list[SolverDiagnostic] = []
        previous_index = -1
        for frame in frames:
            if frame.step_index >= 0 and frame.step_index <= previous_index:
                diagnostics.append(
                    _violation(frame.step_id, "Process frames must preserve recipe order.")
                )
            previous_index = max(previous_index, frame.step_index)
            if not frame.stack_signature:
                diagnostics.append(
                    _violation(frame.step_id, "Process frame is missing stack signature.")
                )
            diagnostics.extend(
                self.check_stack_model(
                    StackGeometry2D(frame.profile.columns),
                    frame.step_id,
                ).diagnostics
            )
        return InvariantCheckResult(tuple(diagnostics))


def _violation(step_id: str, message: str) -> SolverDiagnostic:
    return SolverDiagnostic(
        "error",
        "STACK_INVARIANT_VIOLATION",
        step_id,
        message,
        suggested_repair="Inspect the solver operation that produced this stack.",
        output_usable=False,
    )
