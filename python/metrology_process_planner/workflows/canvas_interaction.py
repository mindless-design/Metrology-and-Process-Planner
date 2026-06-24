"""Pure interaction engine for persistent canvas capture workflows."""

from __future__ import annotations

from dataclasses import replace
from typing import Optional

from metrology_process_planner.domains.geometry import Point
from metrology_process_planner.domains.session import (
    CanvasObjectType,
    SessionRecord,
    SourceViewBinding,
)
from metrology_process_planner.infrastructure.diagnostics_sinks import DiagnosticSink
from metrology_process_planner.infrastructure.trace_context import TraceContext
from metrology_process_planner.workflows.canvas_interaction_box import release_box
from metrology_process_planner.workflows.canvas_interaction_measurement import release_line
from metrology_process_planner.workflows.canvas_interaction_models import (
    InteractionContext,
    InteractionResult,
)
from metrology_process_planner.workflows.canvas_interaction_routing import (
    route_start_drag,
    route_update_drag,
)
from metrology_process_planner.workflows.canvas_state import (
    remove_canvas_object,
    select_canvas_object,
    set_active_parent_object,
)
from metrology_process_planner.workflows.diagnostic_helpers import emit_trace_event


class CanvasInteractionEngine:
    """Coordinate armed capture gestures and persistent canvas records."""

    def __init__(self, diagnostic_sink: Optional[DiagnosticSink] = None) -> None:
        self._diagnostics = diagnostic_sink

    def arm_box_capture(
        self,
        context: InteractionContext,
        parent_id: Optional[str] = None,
        trace_context: Optional[TraceContext] = None,
    ) -> InteractionContext:
        """Return context armed for a Shift-drag site box capture."""
        _emit(self._diagnostics, trace_context, "BoxCaptureArmed", "Box capture armed.")
        return _armed_context(context, CanvasObjectType.SITE_BOX, parent_id)

    def arm_line_capture(
        self,
        context: InteractionContext,
        parent_id: Optional[str],
        trace_context: Optional[TraceContext] = None,
    ) -> InteractionContext:
        """Return context armed for a Shift-drag child measurement line."""
        _emit(self._diagnostics, trace_context, "LineCaptureArmed", "Line capture armed.")
        return _armed_context(context, CanvasObjectType.MEASUREMENT, parent_id)

    def arm_point_capture(
        self,
        context: InteractionContext,
        parent_id: Optional[str] = None,
        trace_context: Optional[TraceContext] = None,
    ) -> InteractionContext:
        """Return context armed for a Shift-click point capture."""
        _emit(self._diagnostics, trace_context, "PointCaptureArmed", "Point capture armed.")
        return _armed_context(context, CanvasObjectType.POINT, parent_id)

    def disarm_capture(self, context: InteractionContext) -> InteractionContext:
        """Return context with no armed capture primitive."""
        return replace(
            context,
            armed_object_type=None,
            live_preview_id=None,
            drag_start=None,
        )

    def start_drag(
        self,
        session: SessionRecord,
        context: InteractionContext,
        start: Point,
        shift_pressed: bool,
        source_view_binding: Optional[SourceViewBinding] = None,
        trace_context: Optional[TraceContext] = None,
    ) -> InteractionResult:
        """Start a live preview when box capture is armed and Shift is pressed."""
        return route_start_drag(
            self._diagnostics,
            session,
            context,
            start,
            shift_pressed,
            source_view_binding,
            trace_context,
        )

    def update_drag(
        self,
        session: SessionRecord,
        context: InteractionContext,
        current: Point,
        shift_pressed: bool,
        trace_context: Optional[TraceContext] = None,
    ) -> InteractionResult:
        """Resize the live preview object during an armed Shift-drag."""
        return route_update_drag(
            self._diagnostics,
            session,
            context,
            current,
            shift_pressed,
            trace_context,
        )

    def release_drag(
        self,
        session: SessionRecord,
        context: InteractionContext,
        end: Point,
        shift_pressed: bool,
        trace_context: Optional[TraceContext] = None,
    ) -> InteractionResult:
        """Commit a live preview into a pending box capture on release."""
        if context.armed_object_type is CanvasObjectType.MEASUREMENT:
            return release_line(
                self._diagnostics,
                session,
                context,
                end,
                shift_pressed,
                trace_context,
            )
        return release_box(
            self._diagnostics,
            session,
            context,
            end,
            shift_pressed,
            trace_context,
        )

    def exit_capture(
        self,
        session: SessionRecord,
        context: InteractionContext,
    ) -> InteractionResult:
        """Clear capture arming and remove only transient live previews."""
        if context.live_preview_id is not None:
            session = remove_canvas_object(session, context.live_preview_id)
        return InteractionResult(session=session, context=self.disarm_capture(context))

    def select_object(self, session: SessionRecord, object_id: str) -> SessionRecord:
        """Select one persistent canvas object by id."""
        return select_canvas_object(session, object_id)

    def set_active_parent(self, session: SessionRecord, object_id: Optional[str]) -> SessionRecord:
        """Mark one persistent canvas object as the active parent."""
        return set_active_parent_object(session, object_id)


def _emit(
    sink: Optional[DiagnosticSink],
    trace_context: Optional[TraceContext],
    event_name: str,
    message: str,
    category: str = "workflow",
    severity: str = "info",
    related_record_ids: tuple[str, ...] = (),
    related_artifact_paths: tuple[str, ...] = (),
) -> None:
    emit_trace_event(
        sink,
        trace_context,
        event_name,
        message,
        category,
        "CanvasInteractionEngine",
        severity,
        related_record_ids,
        related_artifact_paths,
    )


def _armed_context(
    context: InteractionContext,
    object_type: CanvasObjectType,
    parent_id: Optional[str],
) -> InteractionContext:
    return replace(
        context,
        armed_object_type=object_type,
        active_parent_id=parent_id,
        live_preview_id=None,
        drag_start=None,
    )
