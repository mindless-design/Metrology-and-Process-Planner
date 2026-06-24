"""Pure SVG renderer for editable drawing scenes."""

from __future__ import annotations

from collections.abc import Iterable
from html import escape
from typing import Optional

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
from metrology_process_planner.rendering.scene import DrawingScene, ImageLayer
from metrology_process_planner.rendering.styles import DrawingStyle


def render_scene_to_svg(scene: DrawingScene) -> str:
    """Render an editable drawing scene to deterministic SVG text."""

    lines = [
        '<?xml version="1.0" encoding="UTF-8"?>',
        _svg_open(scene),
        _arrow_defs(scene.primitives),
        _background(scene),
    ]
    lines.extend(_image_element(layer) for layer in scene.image_layers)
    lines.extend(_primitive_element(primitive) for primitive in scene.primitives)
    lines.append("</svg>")
    return "\n".join(line for line in lines if line) + "\n"


def _svg_open(scene: DrawingScene) -> str:
    width = scene.canvas.width_px
    height = scene.canvas.height_px
    return (
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" '
        f'viewBox="0 0 {width} {height}" role="img">'
    )


def _arrow_defs(primitives: Iterable[DrawingPrimitive]) -> str:
    if not any(isinstance(mark, LineMark) and _has_arrow(mark) for mark in primitives):
        return ""
    return (
        "<defs>"
        '<marker id="arrow" viewBox="0 0 10 10" refX="8" refY="5" '
        'markerWidth="6" markerHeight="6" orient="auto-start-reverse">'
        '<path d="M 0 0 L 10 5 L 0 10 z" fill="context-stroke" />'
        "</marker>"
        "</defs>"
    )


def _background(scene: DrawingScene) -> str:
    return (
        f'<rect x="0" y="0" width="{scene.canvas.width_px}" '
        f'height="{scene.canvas.height_px}" fill="{escape(scene.canvas.background)}" />'
    )


def _image_element(layer: ImageLayer) -> str:
    return (
        f'<image href="{escape(layer.path)}" x="0" y="0" '
        f'width="{layer.width_px}" height="{layer.height_px}" '
        f'opacity="{_num(layer.opacity)}" preserveAspectRatio="none" />'
    )


def _primitive_element(primitive: DrawingPrimitive) -> str:
    if isinstance(primitive, LineMark):
        return _line_element(primitive)
    if isinstance(primitive, RectangleMark):
        return _rect_element(primitive)
    if isinstance(primitive, EllipseMark):
        return _ellipse_element(primitive)
    if isinstance(primitive, PolylineMark):
        return _points_element("polyline", primitive.points, primitive.style)
    if isinstance(primitive, PolygonMark):
        return _points_element("polygon", primitive.points, primitive.style)
    return _text_element(primitive)


def _line_element(mark: LineMark) -> str:
    marker_start = ' marker-start="url(#arrow)"' if mark.start_marker == "arrow" else ""
    marker_end = ' marker-end="url(#arrow)"' if mark.end_marker == "arrow" else ""
    return (
        f'<line x1="{_num(mark.start.x)}" y1="{_num(mark.start.y)}" '
        f'x2="{_num(mark.end.x)}" y2="{_num(mark.end.y)}" '
        f'{_style_attrs(mark.style, fill_override="none")}{marker_start}{marker_end} />'
    )


def _rect_element(mark: RectangleMark) -> str:
    return (
        f'<rect x="{_num(mark.x)}" y="{_num(mark.y)}" width="{_num(mark.width)}" '
        f'height="{_num(mark.height)}" {_style_attrs(mark.style)} />'
    )


def _ellipse_element(mark: EllipseMark) -> str:
    return (
        f'<ellipse cx="{_num(mark.center.x)}" cy="{_num(mark.center.y)}" '
        f'rx="{_num(mark.radius_x)}" ry="{_num(mark.radius_y)}" '
        f'{_style_attrs(mark.style)} />'
    )


def _points_element(kind: str, points: tuple[CanvasPoint, ...], style: DrawingStyle) -> str:
    joined = " ".join(f"{_num(point.x)},{_num(point.y)}" for point in points)
    return f'<{kind} points="{joined}" {_style_attrs(style)} />'


def _text_element(mark: TextMark) -> str:
    fill = mark.style.fill or mark.style.stroke
    return (
        f'<text x="{_num(mark.position.x)}" y="{_num(mark.position.y)}" '
        f'font-size="{mark.style.font_size_px}" text-anchor="{escape(mark.anchor)}" '
        f'fill="{escape(fill)}" opacity="{_num(mark.style.opacity)}">'
        f"{escape(mark.text)}</text>"
    )


def _style_attrs(style: DrawingStyle, fill_override: Optional[str] = None) -> str:
    fill = fill_override if fill_override is not None else style.fill
    fill_text = "none" if fill is None else escape(fill)
    return (
        f'stroke="{escape(style.stroke)}" fill="{fill_text}" '
        f'stroke-width="{_num(style.stroke_width)}" opacity="{_num(style.opacity)}"'
    )


def _has_arrow(mark: LineMark) -> bool:
    return mark.start_marker == "arrow" or mark.end_marker == "arrow"


def _num(value: float) -> str:
    if float(value).is_integer():
        return str(int(value))
    return f"{value:.6f}".rstrip("0").rstrip(".")
