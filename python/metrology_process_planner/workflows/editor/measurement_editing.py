"""Measurement metadata edit helpers."""

from __future__ import annotations

from dataclasses import replace

from metrology_process_planner.domains.measurement.records import MeasurementRecord

_TEXT_FIELDS = {
    "label": "label",
    "notes": "notes",
    "edge_convention": "edge_detection_convention",
    "edge_detection_convention": "edge_detection_convention",
    "color": "annotation_color",
    "annotation_color": "annotation_color",
}
_FLOAT_FIELDS = {
    "target",
    "lsl",
    "lower_spec_limit",
    "usl",
    "upper_spec_limit",
    "line_weight",
    "line_weight_px",
}


def replace_measurement_field(
    measurement: MeasurementRecord,
    field_key: str,
    value: str,
) -> MeasurementRecord:
    """Return a measurement with one editable metadata field changed."""

    if field_key == "measurement_type":
        return _replace_metadata_value(measurement, field_key, value)
    if field_key in _TEXT_FIELDS:
        return _replace_text(measurement, field_key, value)
    if field_key in _FLOAT_FIELDS:
        return _replace_float(measurement, field_key, value)
    return measurement


def _replace_text(
    measurement: MeasurementRecord,
    field_key: str,
    value: str,
) -> MeasurementRecord:
    if field_key == "label":
        return replace(measurement, label=value)
    if field_key == "notes":
        return replace(measurement, notes=value)
    if _TEXT_FIELDS.get(field_key) == "edge_detection_convention":
        return replace(measurement, edge_detection_convention=value)
    if _TEXT_FIELDS.get(field_key) == "annotation_color":
        return replace(measurement, annotation_color=value.strip().lower())
    return measurement


def _replace_float(
    measurement: MeasurementRecord,
    field_key: str,
    value: str,
) -> MeasurementRecord:
    normalized = _normalized_float_field(field_key)
    if normalized is None:
        return measurement
    if not value.strip():
        return _clear_optional_float(measurement, normalized)
    parsed = _optional_float(value)
    if parsed is None:
        return measurement
    return _replace_float_value(measurement, normalized, parsed)


def _normalized_float_field(field_key: str) -> str | None:
    if field_key in {"lsl", "lower_spec_limit"}:
        return "lower_spec_limit"
    if field_key in {"usl", "upper_spec_limit"}:
        return "upper_spec_limit"
    if field_key == "target":
        return field_key
    if field_key in {"line_weight", "line_weight_px"}:
        return "line_weight"
    return None


def _replace_float_value(
    measurement: MeasurementRecord,
    field_key: str,
    parsed: float,
) -> MeasurementRecord:
    if field_key == "target":
        return replace(measurement, target=parsed)
    if field_key == "lower_spec_limit":
        return replace(measurement, lower_spec_limit=parsed)
    if field_key == "upper_spec_limit":
        return replace(measurement, upper_spec_limit=parsed)
    if field_key == "line_weight":
        return replace(measurement, line_weight=parsed)
    return measurement


def _clear_optional_float(
    measurement: MeasurementRecord,
    field_key: str,
) -> MeasurementRecord:
    if field_key == "target":
        return replace(measurement, target=None)
    if field_key == "lower_spec_limit":
        return replace(measurement, lower_spec_limit=None)
    if field_key == "upper_spec_limit":
        return replace(measurement, upper_spec_limit=None)
    return measurement


def _replace_metadata_value(
    measurement: MeasurementRecord,
    field_key: str,
    value: str,
) -> MeasurementRecord:
    metadata = dict(measurement.metadata or {})
    metadata[field_key] = value
    return replace(measurement, metadata=metadata)


def _optional_float(value: str) -> float | None:
    try:
        return float(value)
    except ValueError:
        return None
