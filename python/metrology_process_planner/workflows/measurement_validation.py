"""Validation helpers for nested capture measurements."""

from __future__ import annotations

import re
from typing import Any

from metrology_process_planner.domains.session import CaptureRecord, SessionRecord
from metrology_process_planner.workflows.measurement_spec_validation import spec_order_errors


def measurement_validation_errors(session: SessionRecord) -> tuple[str, ...]:
    """Return blocking validation errors for saved and pending measurements."""

    errors: list[str] = []
    for capture in session.captures:
        errors.extend(_capture_measurement_errors(capture))
    return tuple(errors)


def measurement_metadata_edit_errors(document: Any) -> tuple[str, ...]:
    """Return blocking errors for malformed unsaved measurement metadata edits."""

    errors: list[str] = []
    edited_measurement_items = set()
    for item_id, field_key, value in document.dirty_state.unsaved_metadata_edits:
        if not _is_measurement_item(document, item_id):
            continue
        if _normalized_spec_field(field_key):
            edited_measurement_items.add(item_id)
        errors.extend(_field_edit_errors(_measurement_id(document, item_id), field_key, value))
    if not errors:
        for item_id in sorted(edited_measurement_items):
            errors.extend(_spec_edit_errors(document, item_id))
    return tuple(errors)


def _capture_measurement_errors(capture: CaptureRecord) -> tuple[str, ...]:
    if not capture.measurements:
        return ()
    if capture.geometry.bounds is None:
        return tuple(
            f"{measurement.id}: parent capture geometry must be a box."
            for measurement in capture.measurements
        )
    return tuple(
        f"{measurement.id}: {warning}"
        for measurement in capture.measurements
        for warning in measurement.validate_against_capture_bounds(capture.geometry.bounds)
    )


def _is_measurement_item(document: Any, item_id: str) -> bool:
    item = document.items_by_id.get(item_id)
    return bool(
        item is not None
        and item.record_ref is not None
        and item.record_ref.record_type == "measurement"
    )


def _measurement_id(document: Any, item_id: str) -> str:
    item = document.items_by_id[item_id]
    return str(item.record_ref.record_id) if item.record_ref is not None else item_id


def _field_edit_errors(measurement_id: str, field_key: str, value: str) -> tuple[str, ...]:
    if _normalized_float_field(field_key):
        return _float_edit_errors(measurement_id, field_key, value)
    if field_key in {"color", "annotation_color"}:
        return _color_edit_errors(measurement_id, value)
    return ()


def _float_edit_errors(measurement_id: str, field_key: str, value: str) -> tuple[str, ...]:
    normalized = _normalized_float_field(field_key)
    if normalized is None:
        return ()
    text = value.strip()
    if not text:
        if normalized == "line_weight":
            return (f"{measurement_id}: Line weight is required.",)
        return ()
    try:
        parsed = float(text)
    except ValueError:
        return (f"{measurement_id}: {_field_label(normalized)} must be a number.",)
    if normalized == "line_weight" and parsed <= 0:
        return (f"{measurement_id}: Line weight must be positive.",)
    return ()


def _color_edit_errors(measurement_id: str, value: str) -> tuple[str, ...]:
    if _HEX_COLOR_RE.fullmatch(value.strip()):
        return ()
    return (f"{measurement_id}: Annotation color must be a hex color.",)


def _normalized_float_field(field_key: str) -> str | None:
    if field_key == "target":
        return "target"
    if field_key in {"lsl", "lower_spec_limit"}:
        return "lower_spec_limit"
    if field_key in {"usl", "upper_spec_limit"}:
        return "upper_spec_limit"
    if field_key in {"line_weight", "line_weight_px"}:
        return "line_weight"
    return None


def _normalized_spec_field(field_key: str) -> str | None:
    normalized = _normalized_float_field(field_key)
    return normalized if normalized in {"target", "lower_spec_limit", "upper_spec_limit"} else None


def _spec_edit_errors(document: Any, item_id: str) -> tuple[str, ...]:
    values = _edited_spec_values(document, item_id)
    if values is None:
        return ()
    measurement_id, target, lower, upper = values
    return spec_order_errors(measurement_id, target, lower, upper)


def _edited_spec_values(
    document: Any,
    item_id: str,
) -> tuple[str, float | None, float | None, float | None] | None:
    measurement = _measurement_for_item(document, item_id)
    if measurement is None:
        return None
    target = measurement.target
    lower = measurement.lower_spec_limit
    upper = measurement.upper_spec_limit
    for edit_item_id, field_key, value in document.dirty_state.unsaved_metadata_edits:
        if edit_item_id != item_id:
            continue
        normalized = _normalized_spec_field(field_key)
        if normalized is None:
            continue
        parsed = _optional_spec_float(value)
        if normalized == "target":
            target = parsed
        elif normalized == "lower_spec_limit":
            lower = parsed
        elif normalized == "upper_spec_limit":
            upper = parsed
    return (_measurement_id(document, item_id), target, lower, upper)


def _measurement_for_item(document: Any, item_id: str) -> Any | None:
    item = document.items_by_id.get(item_id)
    if item is None or item.record_ref is None:
        return None
    measurement_id = item.record_ref.record_id
    parent_id = _record_id_from_item_id(item.record_ref.parent_id)
    for capture in document.session.captures:
        if parent_id is not None and capture.id != parent_id:
            continue
        for measurement in capture.measurements:
            if measurement.id == measurement_id:
                return measurement
    return None


def _optional_spec_float(value: str) -> float | None:
    text = value.strip()
    return None if not text else float(text)


def _record_id_from_item_id(item_id: str | None) -> str | None:
    if item_id is None:
        return None
    if ":" not in item_id:
        return item_id
    return item_id.split(":", 1)[1]


def _field_label(field_key: str) -> str:
    return {
        "target": "Target",
        "lower_spec_limit": "LSL",
        "upper_spec_limit": "USL",
        "line_weight": "Line weight",
    }.get(field_key, field_key)


_HEX_COLOR_RE = re.compile(r"#[0-9a-fA-F]{6}")
