"""Feature-column builders for capture CSV exports."""

from __future__ import annotations

from typing import Any


def feature_columns(capture: Any) -> dict[str, Any]:
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
            "feature_units": geometry.get("units", ""),
        }
    )
    if geometry.get("shape") == "line":
        row.update(_line_feature_columns(geometry))
    if geometry.get("shape") == "point":
        point = dict(geometry.get("point", {}))
        row.update({"feature_point_x": point.get("x", ""), "feature_point_y": point.get("y", "")})
    return row


def _line_feature_columns(geometry: dict[str, Any]) -> dict[str, Any]:
    start = dict(geometry.get("start", {}))
    end = dict(geometry.get("end", {}))
    midpoint = dict(geometry.get("midpoint", {}))
    return {
        "feature_start_x": start.get("x", ""),
        "feature_start_y": start.get("y", ""),
        "feature_end_x": end.get("x", ""),
        "feature_end_y": end.get("y", ""),
        "feature_midpoint_x": midpoint.get("x", ""),
        "feature_midpoint_y": midpoint.get("y", ""),
        "feature_length": geometry.get("length", ""),
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
