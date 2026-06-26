"""Pure workflow helpers for child measurement line capture."""

from __future__ import annotations

from dataclasses import replace

from metrology_process_planner.domains.geometry import Point
from metrology_process_planner.domains.measurement.records import MeasurementRecord
from metrology_process_planner.domains.session import (
    CanvasObject,
    CanvasObjectType,
    CanvasVisualFlag,
    CanvasWorkflowState,
    CaptureGeometry,
    CaptureRecord,
    ModeRegistry,
    SessionRecord,
    WorkflowState,
)
from metrology_process_planner.workflows.canvas_interaction_helpers import next_id
from metrology_process_planner.workflows.canvas_state import (
    find_canvas_object,
    replace_canvas_object,
    select_canvas_object,
    set_active_parent_object,
)
from metrology_process_planner.workflows.measurement_artifacts import (
    ensure_measurement_artifacts,
)
from metrology_process_planner.workflows.measurement_promotion import saved_measurements


def begin_measurement_line(session: SessionRecord, capture_id: str) -> SessionRecord:
    """Return a session armed to capture a child measurement line."""

    parent = _canvas_for_capture(session, capture_id)
    if parent is None:
        return session
    workflow = replace(
        session.workflow,
        active=True,
        stage="measurement_line",
        active_primitive=CanvasObjectType.MEASUREMENT.value,
        pending_item_ref=f"capture:{capture_id}",
    )
    session = replace(session, workflow=workflow)
    session = select_canvas_object(session, parent.id)
    return set_active_parent_object(session, parent.id)


def measurement_parent_unavailable_reason(session: SessionRecord, capture_id: str) -> str:
    """Return why a capture cannot be used as a measurement parent, or empty if ready."""

    capture = _capture_by_id(session, capture_id)
    if capture is None:
        return "Measurements require a saved capture."
    if capture.geometry.bounds is None:
        return "Measurements require a saved box capture."
    parent = _canvas_for_capture(session, capture_id)
    if parent is None or parent.geometry.bounds is None:
        return "Measurements require a saved canvas box for this capture."
    return ""


def add_pending_measurement_line(
    session: SessionRecord,
    parent_canvas_id: str,
    start: Point,
    end: Point,
) -> SessionRecord:
    """Add a pending child measurement and persistent line canvas object."""

    parent = find_canvas_object(session, parent_canvas_id)
    if parent is None or parent.geometry.bounds is None:
        raise ValueError("Measurement line requires a parent site box.")
    capture = _capture_by_id(session, parent.record_id)
    if capture is None:
        raise ValueError("Measurement line requires an existing parent capture.")
    if capture.geometry.bounds is None:
        raise ValueError("Measurement line requires a parent capture box.")
    measurement = _pending_measurement(session, start, end)
    warnings = measurement.validate_against_capture_bounds(parent.geometry.bounds)
    if warnings:
        raise ValueError("; ".join(warnings))
    canvas_object = _measurement_canvas(session, parent, measurement)
    session = _replace_capture_measurements(session, parent.record_id, measurement)
    session = replace_canvas_object(session, canvas_object)
    session = select_canvas_object(session, canvas_object.id)
    return set_active_parent_object(session, parent.id)


def save_pending_measurements(
    session: SessionRecord,
    mode_registry: ModeRegistry | None = None,
) -> SessionRecord:
    """Promote pending measurements and add repairable annotation artifacts."""

    pending_count = _pending_measurement_count(session)
    session = _promote_measurements(session)
    session = _promote_measurement_canvas(session)
    session = ensure_measurement_artifacts(session, mode_registry)
    if pending_count:
        session = _invalidate_exports(session, "measurement added", mode_registry)
    return session


def _invalidate_exports(
    session: SessionRecord,
    reason: str,
    mode_registry: ModeRegistry | None,
) -> SessionRecord:
    from metrology_process_planner.domains.artifacts.artifact_invalidation import (
        invalidate_exports,
    )

    return invalidate_exports(session, reason, mode_registry)


def _canvas_for_capture(session: SessionRecord, capture_id: str) -> CanvasObject | None:
    for canvas_object in session.canvas_objects:
        if canvas_object.record_id == capture_id:
            return canvas_object
    return None


def _capture_by_id(session: SessionRecord, capture_id: str) -> CaptureRecord | None:
    for capture in session.captures:
        if capture.id == capture_id:
            return capture
    return None


def _pending_measurement(session: SessionRecord, start: Point, end: Point) -> MeasurementRecord:
    existing = _existing_measurement_ids(session)
    measurement_id = next_id("meas", existing)
    return MeasurementRecord(
        measurement_id,
        f"Measurement {measurement_id}",
        start,
        end,
        metadata={"workflow_state": "pending"},
    )


def _existing_measurement_ids(session: SessionRecord) -> tuple[str, ...]:
    durable_ids = tuple(
        measurement.id
        for capture in session.captures
        for measurement in capture.measurements
    )
    canvas_ids = tuple(
        item.record_id
        for item in session.canvas_objects
        if item.object_type is CanvasObjectType.MEASUREMENT and item.record_id
    )
    return durable_ids + canvas_ids


def _pending_measurement_count(session: SessionRecord) -> int:
    return sum(
        1
        for capture in session.captures
        for measurement in capture.measurements
        if dict(measurement.metadata or {}).get("workflow_state") == "pending"
    )


def _measurement_canvas(
    session: SessionRecord,
    parent: CanvasObject,
    measurement: MeasurementRecord,
) -> CanvasObject:
    object_id = next_id("canvas", (item.id for item in session.canvas_objects))
    return CanvasObject(
        object_id,
        session.id,
        measurement.id,
        CanvasObjectType.MEASUREMENT,
        parent.id,
        CaptureGeometry.line(measurement.start, measurement.end),
        CanvasWorkflowState.PENDING,
        visual_state=(CanvasVisualFlag.SELECTED,),
    )


def _replace_capture_measurements(
    session: SessionRecord,
    capture_id: str,
    measurement: MeasurementRecord,
) -> SessionRecord:
    captures = tuple(
        capture.add_measurement(measurement) if capture.id == capture_id else capture
        for capture in session.captures
    )
    return replace(session, captures=captures)


def _promote_measurements(session: SessionRecord) -> SessionRecord:
    captures = []
    last_saved_capture_id = session.workflow.last_saved_capture_id
    for capture in session.captures:
        measurements, saved_count = saved_measurements(capture.measurements)
        if saved_count:
            last_saved_capture_id = capture.id
        captures.append(replace(capture, measurements=measurements))
    workflow = WorkflowState(last_saved_capture_id=last_saved_capture_id)
    return replace(session, captures=tuple(captures), workflow=workflow)


def _promote_measurement_canvas(session: SessionRecord) -> SessionRecord:
    objects = tuple(
        replace(item, workflow_state=CanvasWorkflowState.SAVED)
        if item.object_type is CanvasObjectType.MEASUREMENT
        else item
        for item in session.canvas_objects
    )
    return replace(session, canvas_objects=objects)
