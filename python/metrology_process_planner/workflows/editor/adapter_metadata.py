"""Metadata-field builders for the default editor adapter."""

from __future__ import annotations

from metrology_process_planner.domains.measurements import MeasurementRecord
from metrology_process_planner.domains.session import CaptureRecord, PendingCapture, SessionRecord
from metrology_process_planner.workflows.editor.adapter_metadata_lookup import (
    capture_by_id,
    feature_by_id,
    mapping,
    measurement_by_id,
    optional_number,
    pending_by_id,
)
from metrology_process_planner.workflows.editor.adapter_mode_fields import mode_metadata_fields
from metrology_process_planner.workflows.editor.adapter_process import dashboard_fields
from metrology_process_planner.workflows.editor.adapter_process_outputs import (
    process_output_fields,
)
from metrology_process_planner.workflows.editor.document import SessionItem
from metrology_process_planner.workflows.editor.view_models import MetadataField
from metrology_process_planner.workflows.process_capture_extensions import process_solver_request


def metadata_fields_for_item(
    session: SessionRecord,
    item: SessionItem,
) -> tuple[MetadataField, ...]:
    """Return inspector fields for one document item."""

    if item.record_ref is None:
        return dashboard_fields(session)
    if builder := _RECORD_FIELD_BUILDERS.get(item.record_ref.record_type):
        return builder(session, item)
    return ()


def _capture_item_fields(session: SessionRecord, item: SessionItem) -> tuple[MetadataField, ...]:
    if item.record_ref is None:
        return ()
    capture = capture_by_id(session, item.record_ref.record_id)
    return _capture_fields(session, capture) if capture is not None else ()


def _pending_item_fields(session: SessionRecord, item: SessionItem) -> tuple[MetadataField, ...]:
    if item.record_ref is None:
        return ()
    pending = pending_by_id(session, item.record_ref.record_id)
    return _pending_fields(pending) if pending is not None else ()


def _measurement_item_fields(
    session: SessionRecord,
    item: SessionItem,
) -> tuple[MetadataField, ...]:
    if item.record_ref is None:
        return ()
    measurement = measurement_by_id(session, item.record_ref.record_id)
    return _measurement_fields(measurement) if measurement is not None else ()


def _feature_item_fields(session: SessionRecord, item: SessionItem) -> tuple[MetadataField, ...]:
    if item.record_ref is None:
        return ()
    feature = feature_by_id(session, item.record_ref.record_id)
    return _feature_fields(feature) if feature is not None else ()


def _session_drawing_fields(
    _session: SessionRecord,
    item: SessionItem,
) -> tuple[MetadataField, ...]:
    if item.record_ref is None:
        return ()
    return (
        MetadataField("owner_id", "Owner", item.record_ref.parent_id or "", read_only=True),
        MetadataField("role", "Drawing Role", item.role, read_only=True),
    )


def _capture_fields(session: SessionRecord, capture: CaptureRecord) -> tuple[MetadataField, ...]:
    fields = (
        MetadataField("label", "Label", capture.label, required=True),
        MetadataField("notes", "Notes", capture.notes),
        MetadataField("type", "Capture Role", capture.type),
    )
    return fields + _capture_process_fields(session, capture)


def _capture_process_fields(
    session: SessionRecord,
    capture: CaptureRecord,
) -> tuple[MetadataField, ...]:
    process = _capture_process_extension(capture)
    if not process:
        return ()
    recipe = session.process_context.recipe_name or session.process_context.recipe_id or "none"
    return (
        MetadataField("process_recipe", "Recipe", recipe, read_only=True),
        MetadataField(
            "solver_operation",
            "Solver Operation",
            str(process.get("solver_operation", "")),
            read_only=True,
        ),
        MetadataField(
            "process_window",
            "Process Window",
            str(process.get("process_window", "")),
            read_only=True,
        ),
        MetadataField(
            "process_outputs",
            "Process Outputs",
            _capture_output_statuses(session, capture.id),
            read_only=True,
        ),
        MetadataField("process_warnings", "Warnings", str(len(capture.warning_ids))),
    )


def _pending_fields(pending: PendingCapture) -> tuple[MetadataField, ...]:
    metadata = dict(pending.metadata or {})
    compound = dict(metadata.get("compound", {}))
    if not compound:
        return (
            MetadataField("label", "Label", str(metadata.get("label", "")), required=True),
            MetadataField("notes", "Notes", str(metadata.get("notes", ""))),
            MetadataField("capture_role", "Capture Role", pending.object_type.value),
        )
    feature = dict(compound.get("feature", {}))
    fields = (
        MetadataField("label", "Label", str(metadata.get("label", "")), required=True),
        MetadataField("notes", "Notes", str(metadata.get("notes", ""))),
        MetadataField("capture_role", "Capture Role", pending.object_type.value),
        MetadataField("child_role", "Child Role", str(compound.get("child_role", ""))),
        MetadataField("child_kind", "Child Feature", str(compound.get("child_kind", ""))),
        MetadataField("feature_id", "Feature ID", str(feature.get("id", ""))),
        MetadataField("process_context_ref", "Process Context", "process_context.active"),
    )
    return fields + mode_metadata_fields(
        str(compound.get("mode_id", "")),
        metadata,
        exclude={"label", "notes"},
    )


def _measurement_fields(measurement: MeasurementRecord) -> tuple[MetadataField, ...]:
    return (
        MetadataField("label", "Label", measurement.label, required=True),
        MetadataField("target", "Target", optional_number(measurement.target)),
        MetadataField("lower_spec_limit", "LSL", optional_number(measurement.lower_spec_limit)),
        MetadataField("upper_spec_limit", "USL", optional_number(measurement.upper_spec_limit)),
        MetadataField("notes", "Notes", measurement.notes),
        MetadataField(
            "edge_detection_convention",
            "Edge Convention",
            measurement.edge_detection_convention,
        ),
        MetadataField("annotation_color", "Annotation Color", measurement.annotation_color),
        MetadataField("line_weight", "Line Weight", str(measurement.line_weight)),
    )


def _feature_fields(feature: dict[str, object]) -> tuple[MetadataField, ...]:
    geometry = mapping(feature.get("geometry"))
    if str(feature.get("kind", "")) == "point":
        point = mapping(geometry.get("point"))
        return (
            MetadataField("role", "Feature Role", str(feature.get("role", "")), read_only=True),
            MetadataField("x", "X", str(point.get("x", "")), read_only=True),
            MetadataField("y", "Y", str(point.get("y", "")), read_only=True),
        )
    return (
        MetadataField("role", "Feature Role", str(feature.get("role", "")), read_only=True),
        MetadataField("length", "Length", str(geometry.get("length", "")), read_only=True),
    )


def _capture_process_extension(capture: CaptureRecord) -> dict[str, object]:
    solver = process_solver_request(capture)
    if not solver:
        return {}
    return {
        "solver_operation": solver.get("operation", ""),
        "process_window": solver.get("process_window_variant", ""),
    }


def _capture_output_statuses(session: SessionRecord, capture_id: str) -> str:
    statuses = [
        output.status
        for output in session.process_outputs
        if dict(output.metadata or {}).get("capture_id") == capture_id
    ]
    if not statuses:
        return "none"
    counts = {status: statuses.count(status) for status in set(statuses)}
    return ", ".join(f"{status}:{counts[status]}" for status in sorted(counts))


_RECORD_FIELD_BUILDERS = {
    "capture": _capture_item_fields,
    "pending_capture": _pending_item_fields,
    "measurement": _measurement_item_fields,
    "feature": _feature_item_fields,
    "session_drawing": _session_drawing_fields,
    "process_output": process_output_fields,
}
