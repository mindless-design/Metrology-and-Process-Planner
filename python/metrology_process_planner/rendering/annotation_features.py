"""Feature annotation primitives for captured layout images."""

from __future__ import annotations

from typing import Any

from metrology_process_planner.domains.geometry import Point
from metrology_process_planner.rendering.coordinates import CanvasTransform
from metrology_process_planner.rendering.primitives import (
    CanvasPoint,
    DrawingPrimitive,
    EllipseMark,
    LineMark,
    TextMark,
)
from metrology_process_planner.rendering.styles import DrawingStyle
from metrology_process_planner.rendering.theme import render_theme

THEME = render_theme("engineering_dark")


def feature_primitives(
    transform: CanvasTransform,
    feature: object,
) -> list[DrawingPrimitive]:
    """Return visible line or point feature annotation primitives."""

    if not isinstance(feature, dict):
        return []
    geometry = feature.get("geometry", {})
    if not isinstance(geometry, dict):
        return []
    label = str(feature.get("label") or feature.get("role") or feature.get("id") or "")
    if geometry.get("shape") == "line":
        return _line_feature_primitives(transform, geometry, label)
    if geometry.get("shape") == "point":
        return _point_feature_primitives(transform, geometry, label)
    return []


def _line_feature_primitives(
    transform: CanvasTransform,
    geometry: dict[str, Any],
    label: str,
) -> list[DrawingPrimitive]:
    start = transform.map_point(Point.from_dict(geometry["start"]))
    end = transform.map_point(Point.from_dict(geometry["end"]))
    style = DrawingStyle(stroke=THEME.leader, fill=None, stroke_width=4.0, font_size_px=16)
    text = label
    if length := geometry.get("length"):
        text = f"{label} {float(length):.3g}".strip()
    return [
        LineMark(start=start, end=end, style=style, label=label, end_marker="arrow"),
        _endpoint_circle(start, style, "feature start"),
        _endpoint_circle(end, style, "feature end"),
        _feature_label(start, end, text, style),
    ]


def _point_feature_primitives(
    transform: CanvasTransform,
    geometry: dict[str, Any],
    label: str,
) -> list[DrawingPrimitive]:
    center = transform.map_point(Point.from_dict(geometry["point"]))
    style = DrawingStyle(stroke=THEME.leader_warning, fill=None, stroke_width=4.0, font_size_px=16)
    size = 12.0
    label_position = _fit_label_position(
        CanvasPoint(center.x, center.y - size - 6.0),
        label,
        style.font_size_px,
        transform.canvas.width_px,
        transform.canvas.height_px,
    )
    return [
        LineMark(
            CanvasPoint(center.x - size, center.y - size),
            CanvasPoint(center.x + size, center.y + size),
            style,
            label,
        ),
        LineMark(
            CanvasPoint(center.x - size, center.y + size),
            CanvasPoint(center.x + size, center.y - size),
            style,
            label,
        ),
        EllipseMark(center=center, radius_x=size, radius_y=size, style=style, label=label),
        TextMark(
            position=label_position,
            text=label,
            style=DrawingStyle(stroke=style.stroke, fill=style.stroke, font_size_px=16),
        ),
    ]


def _endpoint_circle(point: CanvasPoint, style: DrawingStyle, label: str) -> EllipseMark:
    return EllipseMark(
        center=point,
        radius_x=5.0,
        radius_y=5.0,
        style=DrawingStyle(
            stroke=style.stroke,
            fill=THEME.background,
            stroke_width=style.stroke_width,
            font_size_px=style.font_size_px,
        ),
        label=label,
    )


def _feature_label(
    start: CanvasPoint,
    end: CanvasPoint,
    label: str,
    style: DrawingStyle,
) -> TextMark:
    return TextMark(
        position=CanvasPoint(x=(start.x + end.x) / 2.0, y=(start.y + end.y) / 2.0 - 8.0),
        text=label,
        style=DrawingStyle(stroke=style.stroke, fill=style.stroke, font_size_px=16),
    )


def _fit_label_position(
    position: CanvasPoint,
    text: str,
    font_size_px: float,
    canvas_width_px: int,
    canvas_height_px: int,
) -> CanvasPoint:
    margin = 6.0
    half_width = max(font_size_px, len(text) * font_size_px * 0.28)
    x = min(max(position.x, half_width + margin), canvas_width_px - half_width - margin)
    y = min(max(position.y, font_size_px + margin), canvas_height_px - margin)
    return CanvasPoint(x, y)
