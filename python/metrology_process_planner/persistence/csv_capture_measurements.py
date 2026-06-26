"""Measurement-column builders for capture CSV exports."""

from __future__ import annotations

from collections.abc import Iterable
from typing import Any

from metrology_process_planner.persistence.csv_units import (
    convert_optional_length,
    convert_optional_length_text,
)


def capture_measurement_columns(
    capture: Any,
    canonical_unit: str = "layout",
    display_unit: str = "layout",
) -> dict[str, str]:
    """Return measurement detail and inventory columns for one capture row."""

    first = first_measurement(capture)
    columns = _first_measurement_columns(capture, first, canonical_unit, display_unit)
    columns.update(
        _measurement_inventory_columns(capture.measurements, canonical_unit, display_unit)
    )
    return columns


def first_measurement(capture: Any) -> Any:
    """Return the first measurement attached to a capture, when present."""

    return capture.measurements[0] if capture.measurements else None


def _first_measurement_columns(
    capture: Any,
    first: Any,
    canonical_unit: str,
    display_unit: str,
) -> dict[str, str]:
    if first is None:
        return _capture_measurement_metadata_columns(capture)
    return {
        "measurement_id": first.id,
        "measurement_label": first.label,
        "measurement_type": _measurement_type(first),
        "measurement_start_x": _convert(first.start.x, canonical_unit, display_unit),
        "measurement_start_y": _convert(first.start.y, canonical_unit, display_unit),
        "measurement_end_x": _convert(first.end.x, canonical_unit, display_unit),
        "measurement_end_y": _convert(first.end.y, canonical_unit, display_unit),
        "measurement_length": _convert(first.measured_length, canonical_unit, display_unit),
        "measurement_units": display_unit,
        "target": _convert_optional(first.target, canonical_unit, display_unit),
        "lsl": _convert_optional(first.lower_spec_limit, canonical_unit, display_unit),
        "usl": _convert_optional(first.upper_spec_limit, canonical_unit, display_unit),
        "edge_convention": first.edge_detection_convention,
    }


def _capture_measurement_metadata_columns(capture: Any) -> dict[str, str]:
    metadata = dict(capture.metadata or {})
    columns = _empty_measurement_columns()
    columns.update(
        {
            "measurement_type": str(metadata.get("measurement_type", "")),
            "target": str(metadata.get("target", "")),
            "lsl": str(metadata.get("lsl", "")),
            "usl": str(metadata.get("usl", "")),
            "edge_convention": str(metadata.get("edge_convention", "")),
        }
    )
    return columns


def _empty_measurement_columns() -> dict[str, str]:
    return {
        "measurement_id": "",
        "measurement_label": "",
        "measurement_type": "",
        "measurement_start_x": "",
        "measurement_start_y": "",
        "measurement_end_x": "",
        "measurement_end_y": "",
        "measurement_length": "",
        "measurement_units": "",
        "target": "",
        "lsl": "",
        "usl": "",
        "edge_convention": "",
    }


def _measurement_inventory_columns(
    measurements: Iterable[Any],
    canonical_unit: str,
    display_unit: str,
) -> dict[str, str]:
    return {
        "measurement_ids": _join(measurement.id for measurement in measurements),
        "measurement_labels": _join(measurement.label for measurement in measurements),
        "measurement_types": _join(_measurement_type(measurement) for measurement in measurements),
        "measurement_lengths": _join(
            str(_convert(item.measured_length, canonical_unit, display_unit))
            for item in measurements
        ),
        "measurement_targets": _join(
            _convert_optional(item.target, canonical_unit, display_unit)
            for item in measurements
        ),
        "measurement_lsl": _join(
            _convert_optional(item.lower_spec_limit, canonical_unit, display_unit)
            for item in measurements
        ),
        "measurement_usl": _join(
            _convert_optional(item.upper_spec_limit, canonical_unit, display_unit)
            for item in measurements
        ),
        "measurement_edge_conventions": _join(
            item.edge_detection_convention for item in measurements
        ),
    }


def _join(values: Iterable[object] | object) -> str:
    if values is None:
        return ""
    if isinstance(values, str):
        return values
    if not isinstance(values, Iterable):
        return str(values)
    return ";".join(str(value) for value in values)


def _convert(value: float, canonical_unit: str, display_unit: str) -> float:
    return float(convert_optional_length(value, canonical_unit, display_unit))


def _convert_optional(value: object, canonical_unit: str, display_unit: str) -> str:
    return convert_optional_length_text(value, canonical_unit, display_unit)


def _measurement_type(measurement: Any) -> str:
    metadata = dict(measurement.metadata or {})
    return str(metadata.get("measurement_type", "line") or "line")
