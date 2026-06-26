"""Feature-column builders for capture CSV exports."""

from __future__ import annotations

from typing import Any

from metrology_process_planner.persistence.csv_units import convert_optional_length


def feature_columns(
    capture: Any,
    canonical_unit: str = "layout",
    display_unit: str = "layout",
) -> dict[str, Any]:
    """Return feature metadata columns for one capture row."""

    if not capture.geometry.features:
        return _empty_feature_columns()
    feature = dict(capture.geometry.features[0])
    geometry = dict(feature.get("geometry", {}))
    row = _empty_feature_columns()
    row.update(
        {
            "feature_id": feature.get("id", ""),
            "feature_kind": feature.get("kind", ""),
            "feature_shape": geometry.get("shape", ""),
            "feature_units": display_unit if geometry.get("units", "") else "",
        }
    )
    if geometry.get("shape") == "line":
        row.update(_line_feature_columns(geometry, canonical_unit, display_unit))
    if geometry.get("shape") == "point":
        point = dict(geometry.get("point", {}))
        row.update(
            {
                "feature_point_x": _convert_optional(
                    point.get("x", ""), canonical_unit, display_unit
                ),
                "feature_point_y": _convert_optional(
                    point.get("y", ""), canonical_unit, display_unit
                ),
            }
        )
    return row


def _line_feature_columns(
    geometry: dict[str, Any],
    canonical_unit: str,
    display_unit: str,
) -> dict[str, Any]:
    start = dict(geometry.get("start", {}))
    end = dict(geometry.get("end", {}))
    midpoint = dict(geometry.get("midpoint", {}))
    return {
        "feature_start_x": _convert_optional(start.get("x", ""), canonical_unit, display_unit),
        "feature_start_y": _convert_optional(start.get("y", ""), canonical_unit, display_unit),
        "feature_end_x": _convert_optional(end.get("x", ""), canonical_unit, display_unit),
        "feature_end_y": _convert_optional(end.get("y", ""), canonical_unit, display_unit),
        "feature_midpoint_x": _convert_optional(
            midpoint.get("x", ""), canonical_unit, display_unit
        ),
        "feature_midpoint_y": _convert_optional(
            midpoint.get("y", ""), canonical_unit, display_unit
        ),
        "feature_length": _convert_optional(
            geometry.get("length", ""), canonical_unit, display_unit
        ),
    }


def _empty_feature_columns() -> dict[str, str]:
    return {
        "feature_id": "",
        "feature_kind": "",
        "feature_shape": "",
        "feature_start_x": "",
        "feature_start_y": "",
        "feature_end_x": "",
        "feature_end_y": "",
        "feature_point_x": "",
        "feature_point_y": "",
        "feature_midpoint_x": "",
        "feature_midpoint_y": "",
        "feature_length": "",
        "feature_units": "",
    }


def _convert_optional(value: Any, canonical_unit: str, display_unit: str) -> Any:
    return convert_optional_length(value, canonical_unit, display_unit)
