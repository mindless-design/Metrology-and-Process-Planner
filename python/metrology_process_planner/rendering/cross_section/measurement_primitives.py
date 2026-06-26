"""Drawing primitives for cross-section measurement annotations."""

from __future__ import annotations

from metrology_process_planner.domains.geometry import Point
from metrology_process_planner.rendering.coordinates import CanvasTransform
from metrology_process_planner.rendering.cross_section.measurement_models import (
    MeasurementAnnotation,
)
from metrology_process_planner.rendering.primitives import DrawingPrimitive, LineMark, TextMark
from metrology_process_planner.rendering.styles import DrawingStyle
from metrology_process_planner.rendering.theme import RenderTheme


def measurement_primitives(
    annotations: tuple[MeasurementAnnotation, ...],
    transform: CanvasTransform,
    theme: RenderTheme,
) -> list[DrawingPrimitive]:
    """Return dimension arrows and labels for scene measurement annotations."""

    primitives: list[DrawingPrimitive] = []
    for annotation in annotations:
        start = transform.map_point(Point(*annotation.visual_span[0]))
        end = transform.map_point(Point(*annotation.visual_span[1]))
        label = transform.map_point(Point(*_label_position(annotation)))
        primitives.append(
            LineMark(
                start,
                end,
                DrawingStyle(
                    stroke=theme.leader_warning,
                    fill="none",
                    stroke_width=theme.leader_width_px,
                ),
                annotation.measurement_id,
                "arrow",
                "arrow",
            )
        )
        primitives.append(
            TextMark(
                label,
                f"{annotation.label}: {annotation.formatted_value}",
                DrawingStyle(
                    stroke=theme.warning_text,
                    fill=theme.warning_text,
                    font_size_px=theme.note_size_px,
                ),
                "start",
            )
        )
    return primitives


def _label_position(annotation: MeasurementAnnotation) -> tuple[float, float]:
    start, end = annotation.visual_span
    dx = abs(end[0] - start[0])
    dy = abs(end[1] - start[1])
    if dy >= dx:
        return (annotation.anchor_point[0] + 0.06, annotation.anchor_point[1])
    return (annotation.anchor_point[0], annotation.anchor_point[1] + 0.06)
