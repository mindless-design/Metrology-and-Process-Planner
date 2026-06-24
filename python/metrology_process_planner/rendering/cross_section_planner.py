"""Build editable drawing scenes for process cross-section schematics."""

from __future__ import annotations

from collections.abc import Iterable

from metrology_process_planner.domains.geometry import Box
from metrology_process_planner.domains.process import CrossSectionProfile, Material, StackColumn
from metrology_process_planner.rendering.coordinates import CanvasTransform
from metrology_process_planner.rendering.primitives import (
    CanvasPoint,
    DrawingPrimitive,
    RectangleMark,
    TextMark,
)
from metrology_process_planner.rendering.scene import CanvasSpec, CoordinateFrame, DrawingScene
from metrology_process_planner.rendering.styles import DrawingStyle

DEFAULT_WIDTH_PX = 1200
DEFAULT_HEIGHT_PX = 600


def build_cross_section_drawing_scene(
    profile: CrossSectionProfile,
    materials: Iterable[Material],
    scene_id: str,
    title: str = "",
    include_legend: bool = True,
) -> DrawingScene:
    """Build an editable schematic scene from a cross-section profile."""

    columns = tuple(sorted(profile.columns, key=lambda column: column.x))
    if not columns:
        raise ValueError("Cross-section scenes require at least one stack column.")
    material_colors = {material.id: material.color for material in materials}
    canvas = CanvasSpec(width_px=DEFAULT_WIDTH_PX, height_px=DEFAULT_HEIGHT_PX)
    source_bounds = _profile_bounds(columns)
    transform = CanvasTransform(source_bounds, canvas)
    primitives: list[DrawingPrimitive] = []
    for index, column in enumerate(columns):
        primitives.extend(_column_rectangles(index, columns, column, transform, material_colors))
    if title:
        primitives.append(_title_mark(title))
    if include_legend:
        primitives.extend(_legend_marks(material_colors))
    return DrawingScene(
        id=scene_id,
        role="cross_section",
        canvas=canvas,
        coordinate_frame=CoordinateFrame(source_bounds=source_bounds, y_axis="down", units="model"),
        primitives=tuple(primitives),
        metadata={"title": title},
    )


def _profile_bounds(columns: tuple[StackColumn, ...]) -> Box:
    x_edges = _x_edges(columns)
    z_values = [
        value
        for column in columns
        for interval in column.intervals
        for value in (interval.z_min, interval.z_max)
    ]
    if not z_values:
        z_values = [0.0, 1.0]
    bottom = min(z_values)
    top = max(z_values)
    if bottom == top:
        top = bottom + 1.0
    return Box(left=x_edges[0], bottom=bottom, right=x_edges[-1], top=top)


def _x_edges(columns: tuple[StackColumn, ...]) -> tuple[float, ...]:
    if len(columns) == 1:
        x = columns[0].x
        return (x - 0.5, x + 0.5)
    middle_edges = tuple(
        (columns[index].x + columns[index + 1].x) / 2.0 for index in range(len(columns) - 1)
    )
    first_width = middle_edges[0] - columns[0].x
    last_width = columns[-1].x - middle_edges[-1]
    return (columns[0].x - first_width,) + middle_edges + (columns[-1].x + last_width,)


def _column_rectangles(
    index: int,
    columns: tuple[StackColumn, ...],
    column: StackColumn,
    transform: CanvasTransform,
    material_colors: dict[str, str],
) -> list[RectangleMark]:
    edges = _x_edges(columns)
    rectangles = []
    for interval in column.intervals:
        source = Box(edges[index], interval.z_min, edges[index + 1], interval.z_max)
        x, y, width, height = transform.map_box(source)
        color = material_colors.get(interval.material_id, "#888888")
        rectangles.append(
            RectangleMark(
                x=x,
                y=y,
                width=width,
                height=height,
                style=DrawingStyle(stroke="#333333", fill=color, stroke_width=0.5),
                label=interval.material_id,
            )
        )
    return rectangles


def _title_mark(title: str) -> TextMark:
    return TextMark(
        position=CanvasPoint(x=DEFAULT_WIDTH_PX / 2.0, y=24.0),
        text=title,
        style=DrawingStyle(stroke="#222222", fill="#222222", font_size_px=18),
    )


def _legend_marks(material_colors: dict[str, str]) -> list[DrawingPrimitive]:
    primitives: list[DrawingPrimitive] = []
    for index, material_id in enumerate(sorted(material_colors)):
        y = 40.0 + index * 22.0
        primitives.append(
            RectangleMark(
                x=DEFAULT_WIDTH_PX - 180.0,
                y=y - 12.0,
                width=14.0,
                height=14.0,
                style=DrawingStyle(stroke="#333333", fill=material_colors[material_id]),
                label=material_id,
            )
        )
        primitives.append(
            TextMark(
                position=CanvasPoint(x=DEFAULT_WIDTH_PX - 158.0, y=y),
                text=material_id,
                style=DrawingStyle(stroke="#222222", fill="#222222", font_size_px=12),
                anchor="start",
            )
        )
    return primitives
