"""Point capture commit helpers for canvas interaction."""

from __future__ import annotations

from dataclasses import replace

from metrology_process_planner.domains.geometry import Point
from metrology_process_planner.domains.session import (
    CanvasObject,
    CanvasObjectType,
    CanvasVisualFlag,
    CanvasWorkflowState,
    CaptureGeometry,
    PendingCapture,
    SessionRecord,
)
from metrology_process_planner.workflows.canvas_interaction_helpers import next_id
from metrology_process_planner.workflows.canvas_interaction_models import (
    InteractionContext,
    InteractionResult,
)
from metrology_process_planner.workflows.canvas_state import (
    replace_canvas_object,
    select_canvas_object,
    set_active_parent_object,
)


def commit_pending_point(
    session: SessionRecord,
    context: InteractionContext,
    point: Point,
) -> InteractionResult:
    """Commit a standalone point gesture into a pending capture."""

    pending_id = _next_pending_id(session)
    canvas_id = next_id("canvas", (item.id for item in session.canvas_objects))
    canvas_object = CanvasObject(
        canvas_id,
        session.id,
        pending_id,
        CanvasObjectType.POINT,
        context.active_parent_id,
        CaptureGeometry.point_capture(point),
        CanvasWorkflowState.PENDING,
        visual_state=(CanvasVisualFlag.SELECTED,),
    )
    pending = PendingCapture(
        pending_id,
        session.id,
        canvas_object.id,
        CanvasObjectType.POINT,
        canvas_object.geometry,
        parent_id=context.active_parent_id,
    )
    session = replace(
        replace_canvas_object(session, canvas_object),
        pending_captures=session.pending_captures + (pending,),
    )
    session = select_canvas_object(set_active_parent_object(session, canvas_id), canvas_id)
    return InteractionResult(
        session,
        replace(context, active_parent_id=canvas_id, live_preview_id=None),
    )


def _next_pending_id(session: SessionRecord) -> str:
    indexes = [_sequence(pending.id) for pending in session.pending_captures]
    indexes.extend(_sequence(capture.id) for capture in session.captures)
    index = max(indexes, default=0) + 1
    existing = {pending.id for pending in session.pending_captures}
    while f"pending-{index:03d}" in existing:
        index += 1
    return f"pending-{index:03d}"


def _sequence(record_id: str) -> int:
    suffix = record_id.rsplit("-", 1)[-1]
    return int(suffix) if suffix.isdigit() else 0
