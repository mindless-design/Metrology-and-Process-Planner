"""Execution helpers for process-output regeneration."""

from __future__ import annotations

from dataclasses import replace

from metrology_process_planner.domains.process import (
    HybridCrossSectionSolver,
    ProcessRecipe,
    SolverResult,
)
from metrology_process_planner.domains.session import (
    CaptureRecord,
    SessionMode,
    SessionRecord,
    WarningRecord,
)
from metrology_process_planner.workflows.process_context_support import (
    process_warning,
    with_warnings,
)
from metrology_process_planner.workflows.process_output_requests import (
    ProcessOutputRequest,
    SolverInputBuilder,
)
from metrology_process_planner.workflows.process_output_service import ProcessOutputService
from metrology_process_planner.workflows.process_regeneration_outputs import (
    capture_with_process_output,
    ready_output,
)
from metrology_process_planner.workflows.process_regeneration_records import (
    failed_output,
    upsert_output,
)


def solve_targets(
    session: SessionRecord,
    captures: tuple[CaptureRecord, ...],
    recipe: ProcessRecipe,
) -> tuple[SessionRecord, tuple[WarningRecord, ...], str, str]:
    """Solve process-output targets and update canonical session records."""

    state = _ExecutionState(session)
    builder = SolverInputBuilder()
    for capture in captures:
        request = builder.build_request(session, capture)
        try:
            solver_result = solve_capture_process_output(session, capture, recipe)
        except ValueError as exc:
            state.record_failure(capture, request, exc)
            continue
        state.record_success(capture, request, solver_result)
    return state.result()


def solve_capture_process_output(
    session_or_capture: SessionRecord | CaptureRecord,
    capture_or_recipe: CaptureRecord | ProcessRecipe,
    recipe: ProcessRecipe | None = None,
) -> SolverResult:
    """Solve one process-aware capture for artifact generation."""

    session, capture, recipe = _solver_context(session_or_capture, capture_or_recipe, recipe)
    return HybridCrossSectionSolver().solve(SolverInputBuilder().build(session, capture, recipe))


class _ExecutionState:
    def __init__(self, session: SessionRecord) -> None:
        self.session = session
        self.warnings: list[WarningRecord] = []
        self.outputs = list(session.process_outputs)
        self.artifacts = dict(session.artifacts or {})
        self.captures_by_id = {capture.id: capture for capture in session.captures}
        self.service = ProcessOutputService()

    def record_failure(
        self,
        capture: CaptureRecord,
        request: ProcessOutputRequest,
        exc: ValueError,
    ) -> None:
        warning = process_warning(
            "SOLVER_INPUT_INVALID",
            f"Process output regeneration failed: {exc}",
            "Review the process recipe and capture geometry.",
            capture.id,
        )
        self.warnings.append(warning)
        self.outputs = upsert_output(self.outputs, failed_output(capture, (warning.id,)))
        placeholder = self.service.ensure_placeholder_outputs(
            replace(self.session, process_outputs=tuple(self.outputs), artifacts=self.artifacts),
            (capture,),
            (warning,),
        )
        self.outputs = list(placeholder.process_outputs)
        self.artifacts = dict(placeholder.artifacts or {})
        self.captures_by_id[capture.id] = capture_with_process_output(
            capture, request, {}, "", (warning.id,), None, "failed"
        )

    def record_success(
        self,
        capture: CaptureRecord,
        request: ProcessOutputRequest,
        solver_result: SolverResult,
    ) -> None:
        solver_result_id = f"solver-result-{capture.id}"
        refs, self.artifacts, _superseded = self.service.ensure_ready_artifacts(
            replace(self.session, artifacts=self.artifacts),
            capture,
            request,
            solver_result_id,
        )
        output = ready_output(capture, request, solver_result, refs, solver_result_id)
        self.outputs = upsert_output(self.outputs, output)
        self.captures_by_id[capture.id] = capture_with_process_output(
            capture, request, refs, solver_result_id, (), solver_result, "ready"
        )

    def result(self) -> tuple[SessionRecord, tuple[WarningRecord, ...], str, str]:
        session = replace(
            self.session,
            captures=tuple(
                self.captures_by_id.get(capture.id, capture) for capture in self.session.captures
            ),
            process_outputs=tuple(self.outputs),
            artifacts=self.artifacts,
        )
        if self.warnings:
            result = with_warnings(
                session,
                tuple(self.warnings),
                "warning",
                "Regenerated with warnings.",
            )
            return result.session, result.warnings, result.status, result.message
        return session, (), "success", "Regenerated process outputs."


def _solver_context(
    session_or_capture: SessionRecord | CaptureRecord,
    capture_or_recipe: CaptureRecord | ProcessRecipe,
    recipe: ProcessRecipe | None,
) -> tuple[SessionRecord, CaptureRecord, ProcessRecipe]:
    if recipe is not None:
        return _explicit_solver_context(session_or_capture, capture_or_recipe, recipe)
    if not isinstance(session_or_capture, CaptureRecord):
        raise TypeError("capture is required when recipe is passed as the second argument")
    if not isinstance(capture_or_recipe, ProcessRecipe):
        raise TypeError("recipe must be a ProcessRecipe")
    return _synthetic_solver_context(session_or_capture, capture_or_recipe)


def _explicit_solver_context(
    session: SessionRecord | CaptureRecord,
    capture: CaptureRecord | ProcessRecipe,
    recipe: ProcessRecipe,
) -> tuple[SessionRecord, CaptureRecord, ProcessRecipe]:
    if not isinstance(session, SessionRecord) or not isinstance(capture, CaptureRecord):
        raise TypeError("session and capture are required when recipe is the third argument")
    return session, capture, recipe


def _synthetic_solver_context(
    capture: CaptureRecord,
    recipe: ProcessRecipe,
) -> tuple[SessionRecord, CaptureRecord, ProcessRecipe]:
    session = SessionRecord(
        "solver-input",
        "Solver Input",
        SessionMode.PROCESS_AWARE_METROLOGY,
        capture.created_at,
        capture.created_at,
        captures=(capture,),
    )
    return session, capture, recipe
