"""Pure review actions for pending canvas captures."""

from __future__ import annotations

from dataclasses import replace

from metrology_process_planner.diagnostics.diagnostics_sinks import DiagnosticSink
from metrology_process_planner.diagnostics.trace_context import TraceContext
from metrology_process_planner.domains.session import (
    CanvasObjectType,
    ModeRegistry,
    SessionRecord,
)
from metrology_process_planner.workflows.canvas_interaction_helpers import (
    pending_artifact_paths,
    pending_by_id,
    without_pending,
    without_pending_artifacts,
)
from metrology_process_planner.workflows.canvas_interaction_models import (
    InteractionContext,
    InteractionResult,
)
from metrology_process_planner.workflows.canvas_state import (
    remove_canvas_object,
)
from metrology_process_planner.workflows.pending_capture_canvas import promote_canvas_object
from metrology_process_planner.workflows.pending_capture_save import save_pending_capture


class PendingCaptureReviewService:
    """Convert, retake, or discard pending capture records."""

    def __init__(
        self,
        diagnostic_sink: DiagnosticSink | None = None,
        mode_registry: ModeRegistry | None = None,
    ) -> None:
        self._diagnostics = diagnostic_sink
        self._mode_registry = mode_registry

    def save_pending_box(
        self,
        session: SessionRecord,
        context: InteractionContext,
        pending_id: str,
        label: str = "",
        notes: str = "",
        trace_context: TraceContext | None = None,
    ) -> InteractionResult:
        """Convert one pending box capture into a saved capture record."""

        self._emit(trace_context, "PendingSaveRequested", pending_id, "Save requested.")
        pending = pending_by_id(session, pending_id)
        if pending is None:
            self._emit(trace_context, "PendingSaveMissing", pending_id, "Pending capture missing.")
            return InteractionResult(session=session, context=context, handled=False)
        session, capture_id = save_pending_capture(
            session,
            pending,
            label,
            notes,
            self._mode_registry,
        )
        session = promote_canvas_object(session, pending, capture_id)
        self._emit(
            trace_context,
            "CaptureRecordCreated",
            capture_id,
            "Pending capture promoted to CaptureRecord.",
        )
        return InteractionResult(session=session, context=context)

    def discard_pending(
        self,
        session: SessionRecord,
        context: InteractionContext,
        pending_id: str,
        trace_context: TraceContext | None = None,
    ) -> InteractionResult:
        """Remove one pending capture and its pending canvas object."""

        self._emit(trace_context, "PendingDiscardRequested", pending_id, "Discard requested.")
        pending = pending_by_id(session, pending_id)
        if pending is None:
            return InteractionResult(session=session, context=context, handled=False)
        session = replace(
            session,
            pending_captures=without_pending(session, pending_id),
            artifacts=without_pending_artifacts(dict(session.artifacts or {}), pending_id),
        )
        session = remove_canvas_object(session, pending.canvas_object_id)
        context = replace(context, active_parent_id=pending.parent_id, live_preview_id=None)
        return InteractionResult(
            session=session,
            context=context,
            artifact_paths_to_remove=pending_artifact_paths(pending),
        )

    def retake_pending(
        self,
        session: SessionRecord,
        context: InteractionContext,
        pending_id: str,
        trace_context: TraceContext | None = None,
    ) -> InteractionResult:
        """Discard a pending capture and rearm its original box context."""

        self._emit(trace_context, "PendingRetakeRequested", pending_id, "Retake requested.")
        pending = pending_by_id(session, pending_id)
        if pending is None:
            return InteractionResult(session=session, context=context, handled=False)
        result = self.discard_pending(session, context, pending_id, trace_context)
        return replace(
            result,
            context=replace(
                result.context,
                armed_object_type=CanvasObjectType.SITE_BOX,
                active_parent_id=pending.parent_id,
                live_preview_id=None,
                drag_start=None,
            ),
        )

    def _emit(
        self,
        trace_context: TraceContext | None,
        event_name: str,
        record_id: str,
        message: str,
    ) -> None:
        context = trace_context or (
            TraceContext.new(sink=self._diagnostics) if self._diagnostics is not None else None
        )
        if context is None:
            return
        context.emit(
            event_name,
            {
                "message": message,
                "category": "workflow",
                "source_component": "PendingCaptureReviewService",
                "related_record_ids": (record_id,),
            },
    )

