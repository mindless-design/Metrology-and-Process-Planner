"""Canvas object helpers for pending capture promotion."""

from __future__ import annotations

from dataclasses import replace

from metrology_process_planner.domains.session import (
    CanvasObject,
    CanvasWorkflowState,
    PendingCapture,
    SessionRecord,
)
from metrology_process_planner.workflows.canvas_state import (
    find_canvas_object,
    replace_canvas_object,
)


def promote_canvas_object(
    session: SessionRecord,
    pending: PendingCapture,
    capture_id: str,
) -> SessionRecord:
    """Attach a pending canvas object to the promoted capture record."""

    canvas_object = find_canvas_object(session, pending.canvas_object_id)
    if canvas_object is None:
        return session
    session = _supersede_replaced_canvas_objects(session, pending, capture_id)
    return replace_canvas_object(
        session,
        replace(canvas_object, record_id=capture_id, workflow_state=CanvasWorkflowState.SAVED),
    )


def _supersede_replaced_canvas_objects(
    session: SessionRecord,
    pending: PendingCapture,
    capture_id: str,
) -> SessionRecord:
    metadata = dict(pending.metadata or {})
    if metadata.get("replacement_for") != capture_id:
        return session
    return replace(
        session,
        canvas_objects=tuple(
            _superseded_canvas_object(item, pending, capture_id)
            for item in session.canvas_objects
        ),
    )


def _superseded_canvas_object(
    item: CanvasObject,
    pending: PendingCapture,
    capture_id: str,
) -> CanvasObject:
    if item.id == pending.canvas_object_id or item.record_id != capture_id:
        return item
    return replace(
        item,
        workflow_state=CanvasWorkflowState.SUPERSEDED,
        selectable=False,
        visible=False,
    )
