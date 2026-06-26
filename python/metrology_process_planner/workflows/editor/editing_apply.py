"""Apply editor metadata edits to canonical session records."""

from __future__ import annotations

from dataclasses import replace
from typing import Optional

from metrology_process_planner.domains.artifacts.artifact_invalidation import (
    invalidate_capture_edit,
    invalidate_measurement_edit,
)
from metrology_process_planner.domains.session import (
    CaptureRecord,
    ModeRegistry,
    PendingCapture,
    SessionRecord,
)
from metrology_process_planner.workflows.cad_review_metadata import (
    normalized_cad_review_metadata,
)
from metrology_process_planner.workflows.editor.measurement_editing import (
    replace_measurement_field,
)


def apply_capture_edit(
    session: SessionRecord,
    capture_id: str,
    field_key: str,
    value: str,
    mode_registry: ModeRegistry | None,
) -> SessionRecord:
    """Apply one saved-capture metadata edit."""

    before = _capture_by_id(session, capture_id)
    captures = tuple(
        _replace_capture_field(capture, field_key, value)
        if capture.id == capture_id
        else capture
        for capture in session.captures
    )
    updated = replace(session, captures=captures)
    after = _capture_by_id(updated, capture_id)
    if before is not None and after != before:
        updated = invalidate_capture_edit(updated, capture_id, field_key, mode_registry)
    return updated


def apply_pending_edit(
    session: SessionRecord,
    pending_id: str,
    field_key: str,
    value: str,
) -> SessionRecord:
    """Apply one pending-capture metadata edit."""

    pending_captures = tuple(
        _replace_pending_field(pending, field_key, value)
        if pending.id == pending_id
        else pending
        for pending in session.pending_captures
    )
    return replace(session, pending_captures=pending_captures)


def apply_measurement_edit(
    session: SessionRecord,
    capture_item_id: Optional[str],
    measurement_id: str,
    field_key: str,
    value: str,
    mode_registry: ModeRegistry | None,
) -> SessionRecord:
    """Apply one nested measurement metadata edit."""

    before = _measurement_by_id(session, measurement_id)
    capture_id = _record_id_from_item_id(capture_item_id)
    captures = tuple(
        _replace_measurement_on_capture(capture, measurement_id, field_key, value)
        if capture_id is None or capture.id == capture_id
        else capture
        for capture in session.captures
    )
    updated = replace(session, captures=captures)
    after = _measurement_by_id(updated, measurement_id)
    if before is not None and after != before:
        updated = invalidate_measurement_edit(updated, measurement_id, field_key, mode_registry)
    return updated


def _replace_capture_field(capture: CaptureRecord, field_key: str, value: str) -> CaptureRecord:
    if field_key == "label":
        metadata = dict(capture.metadata or {})
        metadata["label"] = value
        return replace(capture, label=value, metadata=metadata)
    if field_key == "notes":
        return replace(capture, notes=value)
    if field_key in {"type", "capture_type"}:
        metadata = dict(capture.metadata or {})
        metadata["capture_type"] = value
        return replace(capture, type=value, metadata=metadata)
    if field_key in {"role", "capture_role"}:
        metadata = dict(capture.metadata or {})
        metadata["capture_role"] = value
        return replace(capture, role=value, metadata=metadata)
    metadata = dict(capture.metadata or {})
    metadata[field_key] = _metadata_value(field_key, value)
    if _is_cad_review_capture(capture):
        metadata = normalized_cad_review_metadata(metadata)
    return replace(capture, metadata=metadata)


def _replace_pending_field(
    pending: PendingCapture,
    field_key: str,
    value: str,
) -> PendingCapture:
    metadata = dict(pending.metadata or {})
    metadata[field_key] = _metadata_value(field_key, value)
    return replace(pending, metadata=metadata)


def _replace_measurement_on_capture(
    capture: CaptureRecord,
    measurement_id: str,
    field_key: str,
    value: str,
) -> CaptureRecord:
    measurements = tuple(
        replace_measurement_field(measurement, field_key, value)
        if measurement.id == measurement_id
        else measurement
        for measurement in capture.measurements
    )
    return replace(capture, measurements=measurements)


def _is_cad_review_capture(capture: CaptureRecord) -> bool:
    return (
        capture.role == "review_region"
        or capture.type == "cad_review_region"
        or "review_category" in dict(capture.metadata or {})
    )


def _record_id_from_item_id(item_id: Optional[str]) -> Optional[str]:
    if item_id is None:
        return None
    if ":" not in item_id:
        return item_id
    return item_id.split(":", 1)[1]


def _capture_by_id(session: SessionRecord, capture_id: str) -> CaptureRecord | None:
    for capture in session.captures:
        if capture.id == capture_id:
            return capture
    return None


def _measurement_by_id(session: SessionRecord, measurement_id: str) -> object | None:
    for capture in session.captures:
        for measurement in capture.measurements:
            if measurement.id == measurement_id:
                return measurement
    return None


def _metadata_value(field_key: str, value: str) -> str | tuple[str, ...]:
    if field_key != "tags":
        return value
    return tuple(item.strip() for item in value.replace(";", ",").split(",") if item.strip())
