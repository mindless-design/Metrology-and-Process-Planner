"""Theme-aware drawing primitives for cross-section scenes."""

from __future__ import annotations

from metrology_process_planner.domains.geometry import Box, Point
from metrology_process_planner.rendering.coordinates import CanvasTransform
from metrology_process_planner.rendering.cross_section.axis_primitives import axis_primitives
from metrology_process_planner.rendering.cross_section.models import CrossSectionOutputSpec
from metrology_process_planner.rendering.cross_section.note_primitives import note_primitives
from metrology_process_planner.rendering.cross_section.scene_models import CrossSectionSceneModel
from metrology_process_planner.rendering.primitives import (
    CanvasPoint,
    DrawingPrimitive,
    LineMark,
    RectangleMark,
    TextMark,
)
from metrology_process_planner.rendering.styles import DrawingStyle
from metrology_process_planner.rendering.theme import RenderTheme


def rectangle(
    bounds: tuple[float, float, float, float],
    transform: CanvasTransform,
    style: dict[str, str],
    theme: RenderTheme,
) -> RectangleMark:
    """Return a material rectangle styled for the active render theme."""

    x, y, width, height = transform.map_box(Box(*bounds))
    return RectangleMark(
        x,
        y,
        width,
        height,
        DrawingStyle(
            stroke=theme.material_stroke,
            fill=style.get("fill", "#888888"),
            stroke_width=0.8,
            opacity=0.92,
        ),
    )


def label_backdrop(
    bounds: tuple[float, float, float, float],
    transform: CanvasTransform,
    theme: RenderTheme,
) -> RectangleMark:
    """Return a high-contrast label background for the active render theme."""

    left, bottom, right, top = _label_bounds(bounds)
    x, y, width, height = transform.map_box(Box(left - 6.0, bottom - 5.0, right + 8.0, top + 5.0))
    return RectangleMark(
        x,
        y,
        width,
        height,
        DrawingStyle(
            stroke=theme.panel_stroke,
            fill=theme.panel_fill,
            stroke_width=1.2,
            opacity=theme.panel_opacity,
        ),
        "label background",
    )


def text(
    position: tuple[float, float],
    content: str,
    transform: CanvasTransform,
    theme: RenderTheme,
) -> TextMark:
    """Return readable scene label text for the active render theme."""

    point = transform.map_point(Point(position[0], position[1]))
    return TextMark(
        point,
        content,
        DrawingStyle(
            stroke=theme.primary_text,
            fill=theme.primary_text,
            font_size_px=theme.label_size_px,
        ),
        anchor="start",
    )


def leader(
    line: tuple[tuple[float, float], tuple[float, float]],
    transform: CanvasTransform,
    theme: RenderTheme,
) -> LineMark:
    """Return a background-aware leader line."""

    start = transform.map_point(Point(line[0][0], line[0][1]))
    end = transform.map_point(Point(line[1][0], line[1][1]))
    return LineMark(
        start,
        end,
        DrawingStyle(stroke=theme.leader, fill="none", stroke_width=theme.leader_width_px),
    )


def canvas_overlays(
    scene: CrossSectionSceneModel,
    output_spec: CrossSectionOutputSpec,
    theme: RenderTheme,
) -> list[DrawingPrimitive]:
    """Return legend, scale bar, and render-note overlays."""

    primitives: list[DrawingPrimitive] = []
    primitives.extend(axis_primitives(scene, output_spec, theme))
    primitives.extend(_legend_primitives(scene, output_spec, theme))
    primitives.extend(_scale_bar_primitives(scene, output_spec, theme))
    primitives.extend(note_primitives(scene, output_spec, theme))
    return primitives


def _label_bounds(value: tuple[float, float, float, float]) -> tuple[float, float, float, float]:
    x, y, width, height = value
    return (x, y, x + width, y + height)


def _legend_primitives(
    scene: CrossSectionSceneModel,
    output_spec: CrossSectionOutputSpec,
    theme: RenderTheme,
) -> list[DrawingPrimitive]:
    if scene.legend is None or not scene.legend.entries:
        return []
    left = output_spec.width_px - 170.0
    top = 54.0
    height = 26.0 + len(scene.legend.entries) * 20.0
    primitives = _legend_frame(left, top, height, theme)
    for index, entry in enumerate(scene.legend.entries):
        y = top + 16.0 + index * 20.0
        primitives.append(
            RectangleMark(
                left,
                y - 10.0,
                14.0,
                14.0,
                DrawingStyle(stroke=theme.material_stroke, fill=entry.color, stroke_width=1.0),
                entry.material_id,
            )
        )
        label = entry.label if not entry.notes else f"{entry.label} ({', '.join(entry.notes)})"
        primitives.append(
            TextMark(
                CanvasPoint(left + 20.0, y + 1.0),
                label,
                DrawingStyle(stroke=theme.muted_text, fill=theme.muted_text, font_size_px=13),
                "start",
            )
        )
    return primitives


def _legend_frame(
    left: float,
    top: float,
    height: float,
    theme: RenderTheme,
) -> list[DrawingPrimitive]:
    return [
        RectangleMark(
            left - 12.0,
            top - 22.0,
            158.0,
            height,
            DrawingStyle(
                stroke=theme.panel_stroke,
                fill=theme.panel_fill,
                stroke_width=1.0,
                opacity=theme.panel_opacity,
            ),
            "legend",
        ),
        TextMark(
            CanvasPoint(left, top - 5.0),
            "Materials",
            DrawingStyle(stroke=theme.primary_text, fill=theme.primary_text, font_size_px=14),
            anchor="start",
        ),
    ]


def _scale_bar_primitives(
    scene: CrossSectionSceneModel,
    output_spec: CrossSectionOutputSpec,
    theme: RenderTheme,
) -> list[DrawingPrimitive]:
    if not scene.scale_bars:
        return []
    label = str(scene.scale_bars[0].get("label", "scale"))
    y = output_spec.height_px - 34.0
    return [
        LineMark(
            CanvasPoint(56.0, y),
            CanvasPoint(176.0, y),
            DrawingStyle(stroke=theme.scale_bar, fill="none", stroke_width=2.4),
        ),
        TextMark(
            CanvasPoint(116.0, y - 8.0),
            label,
            DrawingStyle(stroke=theme.primary_text, fill=theme.primary_text, font_size_px=13),
        ),
    ]
