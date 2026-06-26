"""Capture feature geometry normalization helpers."""

from __future__ import annotations

from collections.abc import Mapping
from math import hypot
from typing import Any

from metrology_process_planner.domains.geometry import Point


def normalized_feature_payload(feature: Mapping[str, Any]) -> dict[str, Any]:
    """Return a feature payload with deterministic geometry metadata."""

    payload = dict(feature)
    geometry = dict(payload.get("geometry", {}))
    if geometry.get("shape") == "line":
        geometry = _normalized_line_geometry(geometry)
    elif geometry.get("shape") == "point":
        geometry = _normalized_point_geometry(geometry)
    payload["geometry"] = geometry
    if "parent_geometry_id" not in payload:
        payload["parent_geometry_id"] = "primary"
    return payload


def _normalized_line_geometry(geometry: Mapping[str, Any]) -> dict[str, Any]:
    start = Point.from_dict(geometry["start"])
    end = Point.from_dict(geometry["end"])
    midpoint = Point((start.x + end.x) / 2.0, (start.y + end.y) / 2.0)
    return {
        **dict(geometry),
        "shape": "line",
        "start": start.to_dict(),
        "end": end.to_dict(),
        "midpoint": midpoint.to_dict(),
        "length": hypot(end.x - start.x, end.y - start.y),
        "units": str(geometry.get("units", "layout")),
    }


def _normalized_point_geometry(geometry: Mapping[str, Any]) -> dict[str, Any]:
    point = Point.from_dict(geometry["point"])
    return {
        **dict(geometry),
        "shape": "point",
        "point": point.to_dict(),
        "units": str(geometry.get("units", "layout")),
    }
