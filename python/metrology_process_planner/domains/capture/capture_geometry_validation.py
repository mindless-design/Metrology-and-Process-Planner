"""Private validation helpers for capture geometry records."""

from __future__ import annotations

from collections.abc import Mapping
from typing import Any, Optional

from metrology_process_planner.domains.geometry import Box, Point


def validate_box_geometry(bounds: Optional[Box]) -> tuple[str, ...]:
    """Return validation warnings for box capture geometry."""

    if bounds is None:
        return ("Box capture geometry requires bounds.",)
    if bounds.width <= 0 or bounds.height <= 0:
        return ("Box capture geometry requires positive width and height.",)
    return ()


def validate_line_geometry(
    start: Optional[Point],
    end: Optional[Point],
) -> tuple[str, ...]:
    """Return validation warnings for line capture geometry."""

    if start is None or end is None:
        return ("Line capture geometry requires start and end points.",)
    if start == end:
        return ("Line capture geometry requires distinct start and end points.",)
    return ()


def validate_feature_geometry(
    bounds: Optional[Box],
    features: tuple[Mapping[str, Any], ...],
) -> tuple[str, ...]:
    """Return validation warnings for composite feature geometry."""

    if bounds is None and not features:
        return ("Composite or grid capture geometry requires bounds or features.",)
    warnings: list[str] = []
    for feature in features:
        geometry = dict(feature.get("geometry", {}))
        warnings.extend(_validate_point_feature(bounds, geometry))
        warnings.extend(_validate_line_feature(bounds, geometry))
    return tuple(warnings)


def _validate_point_feature(bounds: Optional[Box], geometry: Mapping[str, Any]) -> tuple[str, ...]:
    if geometry.get("shape") != "point" or bounds is None:
        return ()
    point_data = geometry.get("point", {})
    if not isinstance(point_data, Mapping):
        return ()
    point = Point.from_dict(point_data)
    if not bounds.contains_point(point):
        return ("Point feature is outside the parent capture bounds.",)
    return ()


def _validate_line_feature(bounds: Optional[Box], geometry: Mapping[str, Any]) -> tuple[str, ...]:
    if geometry.get("shape") != "line":
        return ()
    start_data = geometry.get("start", {})
    end_data = geometry.get("end", {})
    if not isinstance(start_data, Mapping) or not isinstance(end_data, Mapping):
        return ()
    start = Point.from_dict(start_data)
    end = Point.from_dict(end_data)
    warnings = []
    if start == end:
        warnings.append("Line feature requires distinct start and end points.")
    if bounds is not None and not bounds.contains_segment(start, end):
        warnings.append("Line feature is outside the parent capture bounds.")
    return tuple(warnings)
