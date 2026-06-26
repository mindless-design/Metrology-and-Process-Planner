"""Metadata-field builders for the default editor adapter."""

from __future__ import annotations

from metrology_process_planner.domains.session import (
    CaptureRecord,
    ModeRegistry,
    SessionRecord,
)
from metrology_process_planner.workflows.editor.adapter_capture_metadata import (
    capture_artifact_fields,
    capture_geometry_fields,
)
from metrology_process_planner.workflows.editor.adapter_capture_process_fields import (
    capture_process_fields,
)
from metrology_process_planner.workflows.editor.adapter_feature_metadata import feature_fields
from metrology_process_planner.workflows.editor.adapter_grid_metadata import grid_dataset_fields
from metrology_process_planner.workflows.editor.adapter_measurement_metadata import (
    measurement_fields,
)
from metrology_process_planner.workflows.editor.adapter_metadata_lookup import (
    capture_by_id,
    feature_by_id,
    grid_dataset_by_id,
    measurement_by_id,
    pending_by_id,
    report_by_id,
)
from metrology_process_planner.workflows.editor.adapter_mode_metadata import (
    capture_mode_fields,
)
from metrology_process_planner.workflows.editor.adapter_pending_metadata import (
    cdsem_guidance_fields,
    pending_fields,
)
from metrology_process_planner.workflows.editor.adapter_process import (
    dashboard_fields,
)
from metrology_process_planner.workflows.editor.adapter_process_outputs import (
    process_output_fields,
)
from metrology_process_planner.workflows.editor.adapter_report_metadata import report_fields
from metrology_process_planner.workflows.editor.adapter_setup_metadata import setup_fields
from metrology_process_planner.workflows.editor.document import SessionItem
from metrology_process_planner.workflows.editor.view_models import MetadataField


def metadata_fields_for_item(
    session: SessionRecord,
    item: SessionItem,
    mode_registry: ModeRegistry | None = None,
) -> tuple[MetadataField, ...]:
    """Return inspector fields for one document item."""

    if item.record_ref is None:
        if item.role == "setup":
            return setup_fields(session, mode_registry)
        return dashboard_fields(session, mode_registry)
    if builder := _RECORD_FIELD_BUILDERS.get(item.record_ref.record_type):
        return builder(session, item, mode_registry)
    return ()


def _capture_item_fields(
    session: SessionRecord,
    item: SessionItem,
    mode_registry: ModeRegistry | None = None,
) -> tuple[MetadataField, ...]:
    if item.record_ref is None:
        return ()
    capture = capture_by_id(session, item.record_ref.record_id)
    return _capture_fields(session, capture, mode_registry) if capture is not None else ()


def _pending_item_fields(
    session: SessionRecord,
    item: SessionItem,
    mode_registry: ModeRegistry | None = None,
) -> tuple[MetadataField, ...]:
    if item.record_ref is None:
        return ()
    pending = pending_by_id(session, item.record_ref.record_id)
    return pending_fields(session, pending, mode_registry) if pending is not None else ()


def _measurement_item_fields(
    session: SessionRecord,
    item: SessionItem,
    _mode_registry: ModeRegistry | None = None,
) -> tuple[MetadataField, ...]:
    if item.record_ref is None:
        return ()
    measurement = measurement_by_id(session, item.record_ref.record_id)
    return measurement_fields(measurement) if measurement is not None else ()


def _feature_item_fields(
    session: SessionRecord,
    item: SessionItem,
    _mode_registry: ModeRegistry | None = None,
) -> tuple[MetadataField, ...]:
    if item.record_ref is None:
        return ()
    feature = feature_by_id(session, item.record_ref.record_id)
    return feature_fields(feature) if feature is not None else ()


def _grid_dataset_item_fields(
    session: SessionRecord,
    item: SessionItem,
    _mode_registry: ModeRegistry | None = None,
) -> tuple[MetadataField, ...]:
    if item.record_ref is None:
        return ()
    dataset = grid_dataset_by_id(session, item.record_ref.record_id)
    return grid_dataset_fields(session, dataset) if dataset is not None else ()


def _report_item_fields(
    session: SessionRecord,
    item: SessionItem,
    mode_registry: ModeRegistry | None = None,
) -> tuple[MetadataField, ...]:
    if item.record_ref is None:
        return ()
    report = report_by_id(session, item.record_ref.record_id)
    return report_fields(session, report, mode_registry) if report is not None else ()


def _session_drawing_fields(
    _session: SessionRecord,
    item: SessionItem,
    _mode_registry: ModeRegistry | None = None,
) -> tuple[MetadataField, ...]:
    if item.record_ref is None:
        return ()
    return (
        MetadataField("owner_id", "Owner", item.record_ref.parent_id or "", read_only=True),
        MetadataField("role", "Drawing Role", item.role, read_only=True),
    )


def _capture_fields(
    session: SessionRecord,
    capture: CaptureRecord,
    mode_registry: ModeRegistry | None,
) -> tuple[MetadataField, ...]:
    fields = (
        MetadataField("label", "Label", capture.label, required=True),
        MetadataField("notes", "Notes", capture.notes),
        MetadataField("type", "Capture Role", capture.type),
    )
    return (
        fields
        + cdsem_guidance_fields(session)
        + capture_geometry_fields(session, capture)
        + capture_artifact_fields(session, capture, mode_registry)
        + capture_mode_fields(session, capture, mode_registry)
        + capture_process_fields(session, capture, mode_registry)
    )


_RECORD_FIELD_BUILDERS = {
    "capture": _capture_item_fields,
    "pending_capture": _pending_item_fields,
    "measurement": _measurement_item_fields,
    "feature": _feature_item_fields,
    "grid_dataset": _grid_dataset_item_fields,
    "report": _report_item_fields,
    "session_drawing": _session_drawing_fields,
    "process_output": process_output_fields,
}
