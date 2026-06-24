"""JSON serialization helpers for drawing primitives."""

from __future__ import annotations

from collections.abc import Mapping
from typing import Any

from metrology_process_planner.rendering.primitives import (
    CanvasPoint,
    DrawingPrimitive,
    EllipseMark,
    LineMark,
    PolygonMark,
    PolylineMark,
    RectangleMark,
    TextMark,
)
from metrology_process_planner.rendering.styles import (
    DrawingStyle,
    style_from_dict,
    style_to_dict,
)


def primitive_to_dict(primitive: DrawingPrimitive) -> dict[str, Any]:
    """Serialize a drawing primitive to JSON-compatible data."""

    if isinstance(primitive, LineMark):
        return _line_to_dict(primitive)
    if isinstance(primitive, RectangleMark):
        return _rect_to_dict(primitive)
    if isinstance(primitive, EllipseMark):
        return _ellipse_to_dict(primitive)
    if isinstance(primitive, PolylineMark):
        return _points_mark_to_dict("polyline", primitive.points, primitive.style, primitive.label)
    if isinstance(primitive, PolygonMark):
        return _points_mark_to_dict("polygon", primitive.points, primitive.style, primitive.label)
    return _text_to_dict(primitive)


def primitive_from_dict(data: Mapping[str, Any]) -> DrawingPrimitive:
    """Build a drawing primitive from JSON-compatible data."""

    kind = str(data["kind"])
    if kind == "line":
        return _line_from_dict(data)
    if kind == "rectangle":
        return _rect_from_dict(data)
    if kind == "ellipse":
        return _ellipse_from_dict(data)
    if kind in {"polyline", "polygon"}:
        return _points_mark_from_dict(kind, data)
    if kind == "text":
        return _text_from_dict(data)
    raise ValueError(f"Unknown drawing primitive kind: {kind}")


def point_to_dict(point: CanvasPoint) -> dict[str, float]:
    """Serialize a canvas point to JSON-compatible data."""

    return {"x": point.x, "y": point.y}


def _point_from_dict(data: Mapping[str, Any]) -> CanvasPoint:
    return CanvasPoint(x=float(data["x"]), y=float(data["y"]))


def _line_to_dict(mark: LineMark) -> dict[str, Any]:
    return {
        "kind": "line",
        "start": point_to_dict(mark.start),
        "end": point_to_dict(mark.end),
        "style": style_to_dict(mark.style),
        "label": mark.label,
        "start_marker": mark.start_marker,
        "end_marker": mark.end_marker,
    }


def _line_from_dict(data: Mapping[str, Any]) -> LineMark:
    return LineMark(
        start=_point_from_dict(data["start"]),
        end=_point_from_dict(data["end"]),
        style=style_from_dict(data.get("style", {})),
        label=str(data.get("label", "")),
        start_marker=str(data.get("start_marker", "")),
        end_marker=str(data.get("end_marker", "")),
    )


def _rect_to_dict(mark: RectangleMark) -> dict[str, Any]:
    return {
        "kind": "rectangle",
        "x": mark.x,
        "y": mark.y,
        "width": mark.width,
        "height": mark.height,
        "style": style_to_dict(mark.style),
        "label": mark.label,
    }


def _rect_from_dict(data: Mapping[str, Any]) -> RectangleMark:
    return RectangleMark(
        x=float(data["x"]),
        y=float(data["y"]),
        width=float(data["width"]),
        height=float(data["height"]),
        style=style_from_dict(data.get("style", {})),
        label=str(data.get("label", "")),
    )


def _ellipse_to_dict(mark: EllipseMark) -> dict[str, Any]:
    return {
        "kind": "ellipse",
        "center": point_to_dict(mark.center),
        "radius_x": mark.radius_x,
        "radius_y": mark.radius_y,
        "style": style_to_dict(mark.style),
        "label": mark.label,
    }


def _ellipse_from_dict(data: Mapping[str, Any]) -> EllipseMark:
    return EllipseMark(
        center=_point_from_dict(data["center"]),
        radius_x=float(data["radius_x"]),
        radius_y=float(data["radius_y"]),
        style=style_from_dict(data.get("style", {})),
        label=str(data.get("label", "")),
    )


def _points_mark_to_dict(
    kind: str,
    points: tuple[CanvasPoint, ...],
    style: DrawingStyle,
    label: str,
) -> dict[str, Any]:
    return {
        "kind": kind,
        "points": [point_to_dict(point) for point in points],
        "style": style_to_dict(style),
        "label": label,
    }


def _points_mark_from_dict(kind: str, data: Mapping[str, Any]) -> DrawingPrimitive:
    points = tuple(_point_from_dict(item) for item in data.get("points", ()))
    style = style_from_dict(data.get("style", {}))
    label = str(data.get("label", ""))
    if kind == "polygon":
        return PolygonMark(points=points, style=style, label=label)
    return PolylineMark(points=points, style=style, label=label)


def _text_to_dict(mark: TextMark) -> dict[str, Any]:
    return {
        "kind": "text",
        "position": point_to_dict(mark.position),
        "text": mark.text,
        "style": style_to_dict(mark.style),
        "anchor": mark.anchor,
    }


def _text_from_dict(data: Mapping[str, Any]) -> TextMark:
    return TextMark(
        position=_point_from_dict(data["position"]),
        text=str(data.get("text", "")),
        style=style_from_dict(data.get("style", {})),
        anchor=str(data.get("anchor", "middle")),
    )
