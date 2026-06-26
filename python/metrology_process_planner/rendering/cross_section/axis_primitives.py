"""Axis and tick overlay primitives for cross-section SVG scenes."""

from __future__ import annotations

from collections.abc import Sequence

from metrology_process_planner.rendering.cross_section.models import CrossSectionOutputSpec
from metrology_process_planner.rendering.cross_section.scene_models import CrossSectionSceneModel
from metrology_process_planner.rendering.primitives import (
    CanvasPoint,
    DrawingPrimitive,
    LineMark,
    TextMark,
)
from metrology_process_planner.rendering.styles import DrawingStyle
from metrology_process_planner.rendering.theme import RenderTheme


def axis_primitives(
    scene: CrossSectionSceneModel,
    output_spec: CrossSectionOutputSpec,
    theme: RenderTheme,
) -> list[DrawingPrimitive]:
    """Return engineering axis and tick overlay primitives."""

    if not scene.axes:
        return []
    left = 58.0
    bottom = output_spec.height_px - 62.0
    right = output_spec.width_px - 220.0
    top = 58.0
    primitives: list[DrawingPrimitive] = []
    primitives.extend(_x_axis(scene, left, right, bottom, theme))
    primitives.extend(_z_axis(scene, left, top, bottom, theme))
    return primitives


def _x_axis(
    scene: CrossSectionSceneModel,
    left: float,
    right: float,
    bottom: float,
    theme: RenderTheme,
) -> list[DrawingPrimitive]:
    axis = _axis(scene, "x")
    if not axis:
        return []
    return [
        LineMark(
            CanvasPoint(left, bottom),
            CanvasPoint(right, bottom),
            DrawingStyle(stroke=theme.scale_bar, fill="none", stroke_width=1.2),
        ),
        TextMark(
            CanvasPoint((left + right) / 2.0, bottom + 34.0),
            str(axis.get("label", "x")),
            DrawingStyle(stroke=theme.muted_text, fill=theme.muted_text, font_size_px=13),
        ),
        *_tick_primitives(axis, left, right, bottom, bottom + 7.0, theme, "x"),
    ]


def _z_axis(
    scene: CrossSectionSceneModel,
    left: float,
    top: float,
    bottom: float,
    theme: RenderTheme,
) -> list[DrawingPrimitive]:
    axis = _axis(scene, "z")
    if not axis:
        return []
    return [
        LineMark(
            CanvasPoint(left, bottom),
            CanvasPoint(left, top),
            DrawingStyle(stroke=theme.scale_bar, fill="none", stroke_width=1.2),
        ),
        TextMark(
            CanvasPoint(left - 42.0, top - 16.0),
            str(axis.get("label", "z")),
            DrawingStyle(stroke=theme.muted_text, fill=theme.muted_text, font_size_px=13),
            anchor="start",
        ),
        *_tick_primitives(axis, bottom, top, left, left - 7.0, theme, "z"),
    ]


def _tick_primitives(
    axis: dict[str, object],
    start: float,
    stop: float,
    fixed: float,
    tick_end: float,
    theme: RenderTheme,
    orientation: str,
) -> list[DrawingPrimitive]:
    physical = axis.get("physical_range", (0.0, 1.0))
    if not isinstance(physical, Sequence) or isinstance(physical, str) or len(physical) != 2:
        return []
    low = _float_value(physical[0])
    span = _span(_float_value(physical[0]), _float_value(physical[1]))
    primitives: list[DrawingPrimitive] = []
    ticks = axis.get("ticks", ())
    if not isinstance(ticks, Sequence) or isinstance(ticks, str):
        return primitives
    for item in ticks:
        if isinstance(item, dict):
            primitives.extend(
                _one_tick(item, low, span, start, stop, fixed, tick_end, theme, orientation)
            )
    return primitives


def _one_tick(
    item: dict[str, object],
    low: float,
    span: float,
    start: float,
    stop: float,
    fixed: float,
    tick_end: float,
    theme: RenderTheme,
    orientation: str,
) -> tuple[DrawingPrimitive, DrawingPrimitive]:
    ratio = (_float_value(item.get("value", low)) - low) / span
    pos = start + (stop - start) * ratio
    if orientation == "x":
        line = _tick_line(pos, fixed, pos, tick_end, theme)
        label_point = CanvasPoint(pos, tick_end + 16.0)
    else:
        line = _tick_line(fixed, pos, tick_end, pos, theme)
        label_point = CanvasPoint(tick_end - 4.0, pos + 4.0)
    label = TextMark(
        label_point,
        str(item.get("label", "")),
        DrawingStyle(stroke=theme.muted_text, fill=theme.muted_text, font_size_px=11),
        anchor="middle" if orientation == "x" else "end",
    )
    return (line, label)


def _tick_line(x1: float, y1: float, x2: float, y2: float, theme: RenderTheme) -> LineMark:
    return LineMark(
        CanvasPoint(x1, y1),
        CanvasPoint(x2, y2),
        DrawingStyle(stroke=theme.scale_bar, fill="none", stroke_width=1.0),
    )


def _axis(scene: CrossSectionSceneModel, orientation: str) -> dict[str, object] | None:
    for axis in scene.axes:
        if axis.get("orientation") == orientation or axis.get("axis") == orientation:
            return axis
    return None


def _span(low: float, high: float) -> float:
    return high - low if high != low else 1.0


def _float_value(value: object) -> float:
    if isinstance(value, (int, float, str)):
        return float(value)
    return 0.0
