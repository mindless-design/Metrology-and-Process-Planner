"""Measurement-line release helpers for canvas interaction."""

from __future__ import annotations

from dataclasses import dataclass, replace
from typing import Optional

from metrology_process_planner.diagnostics.diagnostics_sinks import DiagnosticSink
from metrology_process_planner.diagnostics.trace_context import TraceContext
from metrology_process_planner.domains.geometry import Point
from metrology_process_planner.domains.session import CanvasObject, SessionRecord
from metrology_process_planner.workflows.canvas_interaction_commit import invalid_release_result
from metrology_process_planner.workflows.canvas_interaction_drag import update_line_drag
from metrology_process_planner.workflows.canvas_interaction_line import commit_pending_line
from metrology_process_planner.workflows.canvas_interaction_models import (
    InteractionContext,
    InteractionResult,
)
from metrology_process_planner.workflows.canvas_state import (
    find_canvas_object,
    remove_canvas_object,
)
from metrology_process_planner.workflows.compound_capture import (
    add_line_feature,
)
from metrology_process_planner.workflows.compound_capture_routing import active_compound_request
from metrology_process_planner.workflows.measurement_workflow import add_pending_measurement_line


def release_line(
    sink: Optional[DiagnosticSink],
    session: SessionRecord,
    context: InteractionContext,
    end: Point,
    shift_pressed: bool,
    trace_context: Optional[TraceContext],
) -> InteractionResult:
    """Commit a valid line preview into a pending child measurement."""

    updated = update_line_drag(sink, session, context, end, shift_pressed, trace_context)
    if not updated.handled:
        return updated
    ready = _ready_line_release(updated, context, sink, trace_context)
    if ready.result is not None:
        return ready.result
    assert ready.preview is not None
    assert ready.points is not None
    return _commit_ready_line(sink, updated, context, ready, trace_context)


def _commit_ready_line(
    sink: Optional[DiagnosticSink],
    updated: InteractionResult,
    context: InteractionContext,
    ready: _ReadyLineRelease,
    trace_context: Optional[TraceContext],
) -> InteractionResult:
    preview = ready.preview
    points = ready.points
    assert preview is not None
    assert points is not None
    try:
        committed = remove_canvas_object(updated.session, preview.id)
        return _commit_line_feature(
            committed,
            replace(updated.context, live_preview_id=None),
            points[0],
            points[1],
        )
    except ValueError as exc:
        return invalid_release_result(sink, trace_context, updated, preview, (str(exc),))


@dataclass(frozen=True)
class _ReadyLineRelease:
    preview: CanvasObject | None = None
    points: tuple[Point, Point] | None = None
    result: InteractionResult | None = None


def _ready_line_release(
    updated: InteractionResult,
    context: InteractionContext,
    sink: Optional[DiagnosticSink],
    trace_context: Optional[TraceContext],
) -> _ReadyLineRelease:
    preview = find_canvas_object(updated.session, str(context.live_preview_id))
    if preview is None:
        result = InteractionResult(session=updated.session, context=context, handled=False)
        return _empty_ready_release(result)
    points = _line_preview_points(preview)
    if points is None:
        result = InteractionResult(session=updated.session, context=context, handled=False)
        return _empty_ready_release(result)
    warnings = preview.geometry.validate()
    if warnings:
        result = invalid_release_result(sink, trace_context, updated, preview, warnings)
        return _empty_ready_release(result)
    return _ReadyLineRelease(preview, points)


def _empty_ready_release(result: InteractionResult) -> _ReadyLineRelease:
    return _ReadyLineRelease(result=result)


def _line_preview_points(preview: CanvasObject) -> tuple[Point, Point] | None:
    if preview.geometry.start is None or preview.geometry.end is None:
        return None
    return preview.geometry.start, preview.geometry.end


def _commit_line_feature(
    session: SessionRecord,
    context: InteractionContext,
    start: Point,
    end: Point,
) -> InteractionResult:
    request = active_compound_request(session, "line")
    if request is not None and session.workflow.pending_item_ref:
        return InteractionResult(
            add_line_feature(
                session,
                session.workflow.pending_item_ref,
                start,
                end,
                request,
            ),
            context,
        )
    if context.active_parent_id:
        return InteractionResult(
            add_pending_measurement_line(session, context.active_parent_id, start, end),
            context,
        )
    return commit_pending_line(session, context, start, end)
