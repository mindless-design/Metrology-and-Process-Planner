"""Drag routing helpers for canvas interaction."""

from __future__ import annotations

from typing import Optional

from metrology_process_planner.domains.geometry import Point
from metrology_process_planner.domains.session import (
    CanvasObjectType,
    SessionRecord,
    SourceViewBinding,
)
from metrology_process_planner.infrastructure.diagnostics_sinks import DiagnosticSink
from metrology_process_planner.infrastructure.trace_context import TraceContext
from metrology_process_planner.workflows.canvas_interaction_drag import (
    start_box_drag,
    start_line_drag,
    update_box_drag,
    update_line_drag,
)
from metrology_process_planner.workflows.canvas_interaction_models import (
    InteractionContext,
    InteractionResult,
)


def route_start_drag(
    sink: Optional[DiagnosticSink],
    session: SessionRecord,
    context: InteractionContext,
    start: Point,
    shift_pressed: bool,
    source_view_binding: Optional[SourceViewBinding],
    trace_context: Optional[TraceContext],
) -> InteractionResult:
    """Route drag start to the active primitive handler."""

    if context.armed_object_type is CanvasObjectType.MEASUREMENT:
        return start_line_drag(
            sink,
            session,
            context,
            start,
            shift_pressed,
            source_view_binding,
            trace_context,
        )
    return start_box_drag(
        sink,
        session,
        context,
        start,
        shift_pressed,
        source_view_binding,
        trace_context,
    )


def route_update_drag(
    sink: Optional[DiagnosticSink],
    session: SessionRecord,
    context: InteractionContext,
    current: Point,
    shift_pressed: bool,
    trace_context: Optional[TraceContext],
) -> InteractionResult:
    """Route drag update to the active primitive handler."""

    if context.armed_object_type is CanvasObjectType.MEASUREMENT:
        return update_line_drag(sink, session, context, current, shift_pressed, trace_context)
    return update_box_drag(sink, session, context, current, shift_pressed, trace_context)
