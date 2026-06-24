"""Pure pending-measurement review actions."""

from __future__ import annotations

from dataclasses import replace

from metrology_process_planner.domains.session import (
    CanvasObject,
    CanvasObjectType,
    SessionRecord,
    WorkflowState,
)
from metrology_process_planner.workflows.canvas_state import (
    remove_canvas_object,
    select_canvas_object,
    set_active_parent_object,
)
from metrology_process_planner.workflows.measurement_workflow import begin_measurement_line


def discard_pending_measurement(session: SessionRecord, measurement_id: str) -> SessionRecord:
    """Remove a pending measurement and return to the parent capture."""

    parent = _parent_for_measurement(session, measurement_id)
    session = _remove_pending_measurement(session, measurement_id)
    session = _remove_measurement_canvas(session, measurement_id)
    session = replace(session, workflow=WorkflowState())
    if parent is None:
        return session
    parent_canvas_id, _capture_id = parent
    return select_canvas_object(set_active_parent_object(session, None), parent_canvas_id)


def retake_pending_measurement_line(session: SessionRecord, measurement_id: str) -> SessionRecord:
    """Remove a pending measurement and rearm line capture on the same parent."""

    parent = _parent_for_measurement(session, measurement_id)
    session = _remove_pending_measurement(session, measurement_id)
    session = _remove_measurement_canvas(session, measurement_id)
    if parent is None:
        return replace(session, workflow=WorkflowState())
    _parent_canvas_id, capture_id = parent
    return begin_measurement_line(session, capture_id)


def _parent_for_measurement(
    session: SessionRecord,
    measurement_id: str,
) -> tuple[str, str] | None:
    for canvas_object in session.canvas_objects:
        if (
            canvas_object.record_id == measurement_id
            and canvas_object.object_type is CanvasObjectType.MEASUREMENT
            and canvas_object.parent_id
        ):
            parent = _canvas_by_id(session, canvas_object.parent_id)
            if parent is not None:
                return parent.id, parent.record_id
    return None


def _canvas_by_id(session: SessionRecord, canvas_id: str) -> CanvasObject | None:
    for canvas_object in session.canvas_objects:
        if canvas_object.id == canvas_id:
            return canvas_object
    return None


def _remove_pending_measurement(
    session: SessionRecord,
    measurement_id: str,
) -> SessionRecord:
    captures = []
    for capture in session.captures:
        captures.append(
            replace(
                capture,
                measurements=tuple(
                    measurement
                    for measurement in capture.measurements
                    if measurement.id != measurement_id
                    or dict(measurement.metadata or {}).get("workflow_state") != "pending"
                ),
            )
        )
    return replace(session, captures=tuple(captures))


def _remove_measurement_canvas(session: SessionRecord, measurement_id: str) -> SessionRecord:
    current = session
    for canvas_object in session.canvas_objects:
        if canvas_object.record_id == measurement_id:
            current = remove_canvas_object(current, canvas_object.id)
    return current
