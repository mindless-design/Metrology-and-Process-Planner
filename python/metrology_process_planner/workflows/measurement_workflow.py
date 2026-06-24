"""Pure workflow helpers for child measurement line capture."""

from __future__ import annotations

from dataclasses import replace

from metrology_process_planner.domains.geometry import Point
from metrology_process_planner.domains.measurements import MeasurementRecord
from metrology_process_planner.domains.session import (
    ArtifactOwnerRef,
    ArtifactRecord,
    ArtifactRepairMetadata,
    ArtifactStatus,
    CanvasObject,
    CanvasObjectType,
    CanvasVisualFlag,
    CanvasWorkflowState,
    CaptureGeometry,
    SessionRecord,
    WarningRecord,
    WorkflowState,
)
from metrology_process_planner.workflows.canvas_interaction_helpers import next_id
from metrology_process_planner.workflows.canvas_state import (
    find_canvas_object,
    replace_canvas_object,
    select_canvas_object,
    set_active_parent_object,
)


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
    measurement = _pending_measurement(session, start, end)
    warnings = measurement.validate_against_capture_bounds(parent.geometry.bounds)
    if warnings:
        raise ValueError("; ".join(warnings))
    canvas_object = _measurement_canvas(session, parent, measurement)
    session = _replace_capture_measurements(session, parent.record_id, measurement)
    session = replace_canvas_object(session, canvas_object)
    session = select_canvas_object(session, canvas_object.id)
    return set_active_parent_object(session, parent.id)


def save_pending_measurements(session: SessionRecord) -> SessionRecord:
    """Promote pending measurements and add repairable annotation artifacts."""

    session = _promote_measurements(session)
    session = _promote_measurement_canvas(session)
    return _ensure_measurement_artifacts(session)


def _canvas_for_capture(session: SessionRecord, capture_id: str) -> CanvasObject | None:
    for canvas_object in session.canvas_objects:
        if canvas_object.record_id == capture_id:
            return canvas_object
    return None


def _pending_measurement(session: SessionRecord, start: Point, end: Point) -> MeasurementRecord:
    existing = (
        measurement.id
        for capture in session.captures
        for measurement in capture.measurements
    )
    measurement_id = next_id("meas", existing)
    return MeasurementRecord(
        measurement_id,
        f"Measurement {measurement_id}",
        start,
        end,
        metadata={"workflow_state": "pending"},
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
    captures = tuple(
        replace(capture, measurements=_saved(capture.measurements))
        for capture in session.captures
    )
    workflow = WorkflowState(last_saved_capture_id=session.workflow.last_saved_capture_id)
    return replace(session, captures=captures, workflow=workflow)


def _saved(measurements: tuple[MeasurementRecord, ...]) -> tuple[MeasurementRecord, ...]:
    saved = []
    for measurement in measurements:
        metadata = dict(measurement.metadata or {})
        if metadata.get("workflow_state") == "pending":
            metadata["workflow_state"] = "saved"
            saved.append(replace(measurement, metadata=metadata))
        else:
            saved.append(measurement)
    return tuple(saved)


def _promote_measurement_canvas(session: SessionRecord) -> SessionRecord:
    objects = tuple(
        replace(item, workflow_state=CanvasWorkflowState.SAVED)
        if item.object_type is CanvasObjectType.MEASUREMENT
        else item
        for item in session.canvas_objects
    )
    return replace(session, canvas_objects=objects)


def _ensure_measurement_artifacts(session: SessionRecord) -> SessionRecord:
    artifacts = dict(session.artifacts or {})
    warnings = {warning.id: warning for warning in session.warnings}
    captures = []
    for capture in session.captures:
        measurements = []
        for measurement in capture.measurements:
            updated, artifact, warning = _measurement_artifact(measurement, capture.id)
            artifacts[artifact.id] = artifact
            warnings[warning.id] = warning
            measurements.append(updated)
        captures.append(replace(capture, measurements=tuple(measurements)))
    return replace(
        session,
        captures=tuple(captures),
        artifacts=artifacts,
        warnings=tuple(warnings.values()),
    )


def _measurement_artifact(
    measurement: MeasurementRecord,
    capture_id: str,
) -> tuple[MeasurementRecord, ArtifactRecord, WarningRecord]:
    artifact_id = f"measurement-{measurement.id}-annotation"
    warning_id = f"warning-{artifact_id}-pending"
    refs = {**dict(measurement.artifact_refs or {}), "annotation": artifact_id}
    warning_ids = tuple(dict.fromkeys(measurement.warning_ids + (warning_id,)))
    updated = replace(measurement, artifact_refs=refs, warning_ids=warning_ids)
    artifact = ArtifactRecord(
        artifact_id,
        "annotation",
        "Measurement Annotation",
        f"drawings/measurements/{measurement.id}.svg",
        ArtifactOwnerRef("measurement", measurement.id, "annotation"),
        status=ArtifactStatus.PENDING,
        generator="measurement_workflow",
        repair=ArtifactRepairMetadata("regenerate_artifact", "Generate measurement annotation."),
        warning_ids=(warning_id,),
        extensions={"capture_id": capture_id},
    )
    warning = WarningRecord(
        warning_id,
        "Measurement annotation artifact has not been generated yet.",
        related_item_refs=(f"measurement:{measurement.id}",),
        related_artifact_refs=(artifact_id,),
        repair_suggestion="Regenerate the measurement annotation artifact.",
    )
    return updated, artifact, warning
