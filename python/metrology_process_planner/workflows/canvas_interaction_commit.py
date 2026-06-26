"""Commit helpers for canvas interaction release transitions."""

from __future__ import annotations

from dataclasses import replace
from typing import Optional

from metrology_process_planner.diagnostics.diagnostics_sinks import DiagnosticSink
from metrology_process_planner.diagnostics.trace_context import TraceContext
from metrology_process_planner.domains.session import (
    CanvasObject,
    CanvasVisualFlag,
    CanvasWorkflowState,
    ModeRegistry,
    PendingCapture,
    SessionRecord,
)
from metrology_process_planner.workflows.canvas_interaction_helpers import (
    pending_crop_artifact,
    with_visual_flag,
)
from metrology_process_planner.workflows.canvas_interaction_models import InteractionResult
from metrology_process_planner.workflows.canvas_state import (
    replace_canvas_object,
    select_canvas_object,
    set_active_parent_object,
)
from metrology_process_planner.workflows.capture_auto_save import (
    auto_save_pending_capture,
    should_auto_save_capture,
)
from metrology_process_planner.workflows.capture_readiness import (
    capture_blocked_by_setup_message,
)
from metrology_process_planner.workflows.capture_replacement import (
    replacement_metadata,
    review_workflow,
)
from metrology_process_planner.workflows.diagnostic_helpers import emit_trace_event, trace_ids
from metrology_process_planner.workflows.setup_capture_commit import commit_setup_box_if_active


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
    mode_registry: ModeRegistry | None = None,
) -> InteractionResult:
    """Commit a valid preview object into a pending capture."""

    setup_result = _setup_capture_result(sink, trace_context, updated, preview, mode_registry)
    if setup_result is not None:
        return setup_result
    pending_id = _next_pending_id(updated.session)
    image_path = f"images/{pending_id}.png"
    ids = trace_ids(
        trace_context,
        canvas_object_trace_id=preview.id,
        capture_trace_id=pending_id,
        artifact_trace_id=image_path,
    )
    metadata = replacement_metadata(updated.session)
    pending = PendingCapture(
        id=pending_id,
        session_id=updated.session.id,
        canvas_object_id=preview.id,
        object_type=preview.object_type,
        geometry=preview.geometry,
        parent_id=preview.parent_id,
        image_artifact_path=image_path,
        source_view_binding=preview.source_view_binding,
        metadata=metadata,
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
        workflow=review_workflow(updated.session, metadata),
    )
    session = select_canvas_object(set_active_parent_object(session, committed.id), committed.id)
    context = replace(updated.context, active_parent_id=committed.id, live_preview_id=None)
    _emit_pending_created(sink, trace_context, committed.id, pending_id, image_path)
    if should_auto_save_capture(session, metadata, mode_registry):
        return auto_save_pending_capture(session, context, pending_id, image_path, mode_registry)
    return InteractionResult(session=session, context=context, artifact_requests=(image_path,))


def _setup_capture_result(
    sink: Optional[DiagnosticSink],
    trace_context: Optional[TraceContext],
    updated: InteractionResult,
    preview: CanvasObject,
    mode_registry: ModeRegistry | None,
) -> InteractionResult | None:
    setup_result = commit_setup_box_if_active(updated.session, updated.context, preview)
    if setup_result is not None:
        _emit_setup_created(sink, trace_context, preview.id, setup_result.artifact_requests)
        return setup_result
    setup_block = capture_blocked_by_setup_message(updated.session, mode_registry)
    if setup_block:
        return invalid_release_result(sink, trace_context, updated, preview, (setup_block,))
    return None


def _emit_setup_created(
    sink: Optional[DiagnosticSink],
    trace_context: Optional[TraceContext],
    canvas_id: str,
    artifact_paths: tuple[str, ...],
) -> None:
    _emit(
        sink,
        trace_context.with_canvas_object(canvas_id) if trace_context else None,
        "SetupCaptureCreated",
        "Geometry committed into setup capture.",
        category="workflow",
        related_record_ids=(canvas_id,),
        related_artifact_paths=artifact_paths,
    )


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


def _next_pending_id(session: SessionRecord) -> str:
    existing_ids = {pending.id for pending in session.pending_captures}
    indexes = [_pending_sequence(pending.id) for pending in session.pending_captures]
    indexes.extend(_capture_sequence(capture) for capture in session.captures)
    index = max(indexes, default=0) + 1
    while f"pending-{index:03d}" in existing_ids:
        index += 1
    return f"pending-{index:03d}"


def _pending_sequence(pending_id: str) -> int:
    suffix = pending_id.rsplit("-", 1)[-1]
    return int(suffix) if suffix.isdigit() else 0


def _capture_sequence(capture: object) -> int:
    sequence = int(getattr(capture, "sequence", 0) or 0)
    if sequence > 0:
        return sequence
    suffix = str(getattr(capture, "id", "")).rsplit("-", 1)[-1]
    return int(suffix) if suffix.isdigit() else 0


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
