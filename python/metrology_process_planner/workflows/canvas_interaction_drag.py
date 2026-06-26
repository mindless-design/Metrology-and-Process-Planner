"""Drag start and update helpers for canvas interaction workflows."""

from __future__ import annotations

from dataclasses import replace
from typing import Optional

from metrology_process_planner.diagnostics.diagnostics_sinks import DiagnosticSink
from metrology_process_planner.diagnostics.trace_context import TraceContext
from metrology_process_planner.domains.geometry import Box, Point
from metrology_process_planner.domains.session import (
    CanvasObject,
    CanvasObjectType,
    CanvasWorkflowState,
    CaptureGeometry,
    SessionRecord,
    SourceViewBinding,
)
from metrology_process_planner.workflows.canvas_interaction_helpers import (
    box_capture_is_active,
    line_capture_is_active,
    line_live_preview,
    live_preview,
    next_id,
)
from metrology_process_planner.workflows.canvas_interaction_models import (
    InteractionContext,
    InteractionResult,
)
from metrology_process_planner.workflows.canvas_state import replace_canvas_object
from metrology_process_planner.workflows.diagnostic_helpers import emit_trace_event, trace_ids


def start_box_drag(
    sink: Optional[DiagnosticSink],
    session: SessionRecord,
    context: InteractionContext,
    start: Point,
    shift_pressed: bool,
    source_view_binding: Optional[SourceViewBinding],
    trace_context: Optional[TraceContext],
) -> InteractionResult:
    """Start a live preview object for an armed Shift-drag."""

    if not box_capture_is_active(context, shift_pressed):
        _emit(sink, trace_context, "GestureIgnored", "Drag ignored.", "gesture")
        return InteractionResult(session=session, context=context, handled=False)
    object_id = next_id("canvas", (item.id for item in session.canvas_objects))
    canvas_object = CanvasObject(
        id=object_id,
        session_id=session.id,
        record_id=object_id,
        object_type=CanvasObjectType.SITE_BOX,
        parent_id=context.active_parent_id,
        geometry=CaptureGeometry.box(Box(start.x, start.y, start.x, start.y)),
        workflow_state=CanvasWorkflowState.LIVE_PREVIEW,
        source_view_binding=source_view_binding or SourceViewBinding(),
        trace_ids=trace_ids(trace_context, canvas_object_trace_id=object_id),
    )
    session = replace_canvas_object(session, canvas_object)
    context = replace(context, live_preview_id=object_id, drag_start=start)
    _emit(sink, trace_context, "LivePreviewCreated", "Live preview created.", "canvas", object_id)
    return InteractionResult(session=session, context=context)


def update_box_drag(
    sink: Optional[DiagnosticSink],
    session: SessionRecord,
    context: InteractionContext,
    current: Point,
    shift_pressed: bool,
    trace_context: Optional[TraceContext],
) -> InteractionResult:
    """Resize the current live preview object."""

    preview = live_preview(session, context, shift_pressed)
    if preview is None or context.drag_start is None:
        return InteractionResult(session=session, context=context, handled=False)
    updated = replace(
        preview,
        geometry=CaptureGeometry.box(
            Box(context.drag_start.x, context.drag_start.y, current.x, current.y)
        ),
    )
    _emit(sink, trace_context, "LivePreviewUpdated", "Live preview updated.", "canvas", preview.id)
    return InteractionResult(session=replace_canvas_object(session, updated), context=context)


def start_line_drag(
    sink: Optional[DiagnosticSink],
    session: SessionRecord,
    context: InteractionContext,
    start: Point,
    shift_pressed: bool,
    source_view_binding: Optional[SourceViewBinding],
    trace_context: Optional[TraceContext],
) -> InteractionResult:
    """Start a live preview for an armed child measurement line."""

    if not line_capture_is_active(context, shift_pressed):
        _emit(sink, trace_context, "GestureIgnored", "Line drag ignored.", "gesture")
        return InteractionResult(session=session, context=context, handled=False)
    object_id = next_id("canvas", (item.id for item in session.canvas_objects))
    canvas_object = CanvasObject(
        id=object_id,
        session_id=session.id,
        record_id=object_id,
        object_type=CanvasObjectType.MEASUREMENT,
        parent_id=context.active_parent_id,
        geometry=CaptureGeometry.line(start, start),
        workflow_state=CanvasWorkflowState.LIVE_PREVIEW,
        source_view_binding=source_view_binding or SourceViewBinding(),
        trace_ids=trace_ids(trace_context, canvas_object_trace_id=object_id),
    )
    session = replace_canvas_object(session, canvas_object)
    context = replace(context, live_preview_id=object_id, drag_start=start)
    _emit(sink, trace_context, "LinePreviewCreated", "Line preview created.", "canvas", object_id)
    return InteractionResult(session=session, context=context)


def update_line_drag(
    sink: Optional[DiagnosticSink],
    session: SessionRecord,
    context: InteractionContext,
    current: Point,
    shift_pressed: bool,
    trace_context: Optional[TraceContext],
) -> InteractionResult:
    """Resize the current child measurement line preview."""

    preview = line_live_preview(session, context, shift_pressed)
    if preview is None or context.drag_start is None:
        return InteractionResult(session=session, context=context, handled=False)
    updated = replace(preview, geometry=CaptureGeometry.line(context.drag_start, current))
    _emit(sink, trace_context, "LinePreviewUpdated", "Line preview updated.", "canvas", preview.id)
    return InteractionResult(session=replace_canvas_object(session, updated), context=context)


def _emit(
    sink: Optional[DiagnosticSink],
    trace_context: Optional[TraceContext],
    event_name: str,
    message: str,
    category: str,
    record_id: str = "",
) -> None:
    context = (
        trace_context.with_canvas_object(record_id)
        if trace_context and record_id
        else trace_context
    )
    emit_trace_event(
        sink,
        context,
        event_name,
        message,
        category,
        "CanvasInteractionEngine",
        related_record_ids=(record_id,) if record_id else (),
    )
