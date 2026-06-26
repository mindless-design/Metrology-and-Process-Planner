"""Geometry helpers for overview extraction, layout, and collision checks."""

from __future__ import annotations

from collections.abc import Iterable, Mapping
from typing import Any

from metrology_process_planner.domains.geometry import Box, Point


def box_union(boxes: Iterable[Box]) -> Box:
    """Return bounds containing all input boxes."""

    normalized = [box.normalized() for box in boxes]
    if not normalized:
        return Box(0, 0, 1000, 700)
    return Box(
        min(box.left for box in normalized),
        min(box.bottom for box in normalized),
        max(box.right for box in normalized),
        max(box.top for box in normalized),
    )


def boxes_overlap(first: Box, second: Box, padding: float = 0.0) -> bool:
    """Return whether two normalized boxes overlap with optional padding."""

    a = first.normalized()
    b = second.normalized()
    return not (
        a.right + padding <= b.left
        or b.right + padding <= a.left
        or a.top + padding <= b.bottom
        or b.top + padding <= a.bottom
    )


def box_from_geometry(data: Mapping[str, Any]) -> Box | None:
    """Build a bounding box from a generic saved geometry payload."""

    kind = str(data.get("kind", ""))
    if kind == "box" and isinstance(data.get("bounds"), Mapping):
        return Box.from_dict(data["bounds"])
    if kind == "point" and isinstance(data.get("point"), Mapping):
        point = Point.from_dict(data["point"])
        return padded_point_box(point)
    if (
        kind == "line"
        and isinstance(data.get("start"), Mapping)
        and isinstance(data.get("end"), Mapping)
    ):
        start = Point.from_dict(data["start"])
        end = Point.from_dict(data["end"])
        return Box(
            min(start.x, end.x),
            min(start.y, end.y),
            max(start.x, end.x),
            max(start.y, end.y),
        )
    return None


def padded_point_box(point: Point, radius: float = 4.0) -> Box:
    """Return a small box used for point target collision checks."""

    return Box(point.x - radius, point.y - radius, point.x + radius, point.y + radius)


def segment_intersects_box(start: Point, end: Point, box: Box) -> bool:
    """Return whether a segment intersects an axis-aligned box."""

    bounds = box.normalized()
    if bounds.contains_point(start) or bounds.contains_point(end):
        return True
    edges = (
        (Point(bounds.left, bounds.bottom), Point(bounds.right, bounds.bottom)),
        (Point(bounds.right, bounds.bottom), Point(bounds.right, bounds.top)),
        (Point(bounds.right, bounds.top), Point(bounds.left, bounds.top)),
        (Point(bounds.left, bounds.top), Point(bounds.left, bounds.bottom)),
    )
    return any(
        segments_intersect(start, end, edge_start, edge_end)
        for edge_start, edge_end in edges
    )


def segments_intersect(a: Point, b: Point, c: Point, d: Point) -> bool:
    """Return whether two line segments intersect."""

    o1 = _orientation(a, b, c)
    o2 = _orientation(a, b, d)
    o3 = _orientation(c, d, a)
    o4 = _orientation(c, d, b)
    if o1 * o2 < 0 and o3 * o4 < 0:
        return True
    return _collinear_segment_hit(a, b, c, d, (o1, o2, o3, o4))


def _orientation(p: Point, q: Point, r: Point) -> float:
    return (q.y - p.y) * (r.x - q.x) - (q.x - p.x) * (r.y - q.y)


def _on_segment(p: Point, q: Point, r: Point) -> bool:
    return min(p.x, r.x) <= q.x <= max(p.x, r.x) and min(p.y, r.y) <= q.y <= max(p.y, r.y)


def _collinear_segment_hit(
    a: Point,
    b: Point,
    c: Point,
    d: Point,
    orientations: tuple[float, float, float, float],
) -> bool:
    eps = 1e-9
    o1, o2, o3, o4 = orientations
    return (
        _is_collinear(o1, eps) and _on_segment(a, c, b)
        or _is_collinear(o2, eps) and _on_segment(a, d, b)
        or _is_collinear(o3, eps) and _on_segment(c, a, d)
        or _is_collinear(o4, eps) and _on_segment(c, b, d)
    )


def _is_collinear(value: float, eps: float) -> bool:
    return abs(value) < eps
