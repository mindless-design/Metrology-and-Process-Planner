"""Commit helpers for canvas interaction release transitions."""

from __future__ import annotations

from dataclasses import replace
from typing import Optional

from metrology_process_planner.domains.session import (
    CanvasObject,
    CanvasVisualFlag,
    CanvasWorkflowState,
    PendingCapture,
)
from metrology_process_planner.infrastructure.diagnostics_sinks import DiagnosticSink
from metrology_process_planner.infrastructure.trace_context import TraceContext
from metrology_process_planner.workflows.canvas_interaction_helpers import (
    next_id,
    pending_crop_artifact,
    with_visual_flag,
)
from metrology_process_planner.workflows.canvas_interaction_models import InteractionResult
from metrology_process_planner.workflows.canvas_state import (
    replace_canvas_object,
    select_canvas_object,
    set_active_parent_object,
)
from metrology_process_planner.workflows.diagnostic_helpers import emit_trace_event, trace_ids


def invalid_release_result(
    sink: Optional[DiagnosticSink],
    trace_context: Optional[TraceContext],
    updated: InteractionResult,
    preview: CanvasObject,
    warnings: tuple[str, ...],
) -> InteractionResult:
    """Return an invalid release result and emit validation diagnostics."""

    invalid = with_visual_flag(preview, CanvasVisualFlag.INVALID)
    session = replace_canvas_object(updated.session, invalid)
    _emit(
        sink,
        trace_context.with_canvas_object(preview.id) if trace_context else None,
        "GeometryValidationFailed",
        "; ".join(warnings),
        category="validation",
        severity="warning",
        related_record_ids=(preview.id,),
    )
    return InteractionResult(session=session, context=updated.context, messages=warnings)


def commit_pending_box(
    sink: Optional[DiagnosticSink],
    trace_context: Optional[TraceContext],
    updated: InteractionResult,
    preview: CanvasObject,
) -> InteractionResult:
    """Commit a valid preview object into a pending capture."""

    pending_id = next_id("pending", (item.id for item in updated.session.pending_captures))
    image_path = f"images/{pending_id}.png"
    ids = trace_ids(
        trace_context,
        canvas_object_trace_id=preview.id,
        capture_trace_id=pending_id,
        artifact_trace_id=image_path,
    )
    pending = PendingCapture(
        id=pending_id,
        session_id=updated.session.id,
        canvas_object_id=preview.id,
        object_type=preview.object_type,
        geometry=preview.geometry,
        parent_id=preview.parent_id,
        image_artifact_path=image_path,
        source_view_binding=preview.source_view_binding,
        trace_ids=ids,
    )
    committed = replace(preview, record_id=pending_id, workflow_state=CanvasWorkflowState.PENDING)
    artifacts = dict(updated.session.artifacts or {})
    artifact = pending_crop_artifact(pending)
    if artifact is not None:
        artifacts[artifact.id] = artifact
    session = replace(
        replace_canvas_object(updated.session, committed),
        pending_captures=updated.session.pending_captures + (pending,),
        artifacts=artifacts,
    )
    session = select_canvas_object(set_active_parent_object(session, committed.id), committed.id)
    context = replace(updated.context, active_parent_id=committed.id, live_preview_id=None)
    _emit_pending_created(sink, trace_context, committed.id, pending_id, image_path)
    return InteractionResult(session=session, context=context, artifact_requests=(image_path,))


def _emit_pending_created(
    sink: Optional[DiagnosticSink],
    trace_context: Optional[TraceContext],
    canvas_id: str,
    pending_id: str,
    image_path: str,
) -> None:
    _emit(
        sink,
        trace_context.with_canvas_object(canvas_id) if trace_context else None,
        "PendingCaptureCreated",
        "Geometry committed into pending capture.",
        category="workflow",
        related_record_ids=(canvas_id, pending_id),
        related_artifact_paths=(image_path,),
    )


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
