"""Point-stack schematic drawing adapter."""

from __future__ import annotations

from metrology_process_planner.domains.session.display_units import format_length
from metrology_process_planner.rendering.cross_section.models import CrossSectionOutputSpec
from metrology_process_planner.rendering.cross_section.scene_models import (
    CrossSectionSceneModel,
    MaterialShape,
)
from metrology_process_planner.rendering.primitives import (
    CanvasPoint,
    DrawingPrimitive,
    RectangleMark,
    TextMark,
)
from metrology_process_planner.rendering.scene import CanvasSpec, CoordinateFrame, DrawingScene
from metrology_process_planner.rendering.styles import DrawingStyle
from metrology_process_planner.rendering.theme import (
    RenderTheme,
    contrast_text_for_fill,
)


def point_stack_drawing_scene(
    scene: CrossSectionSceneModel,
    output_spec: CrossSectionOutputSpec,
    theme: RenderTheme,
) -> DrawingScene:
    """Render ellipsometry point samples as an ordered material stack schematic."""

    canvas = CanvasSpec(output_spec.width_px, output_spec.height_px, background=theme.background)
    stack = _point_stack_shapes(scene)
    primitives: list[DrawingPrimitive] = [
        TextMark(
            CanvasPoint(64.0, 56.0),
            scene.title or "Point stack schematic",
            DrawingStyle(stroke=theme.primary_text, fill=theme.primary_text, font_size_px=24),
            anchor="start",
        ),
        TextMark(
            CanvasPoint(64.0, 84.0),
            "Ordered material stack at selected point",
            DrawingStyle(stroke=theme.secondary_text, fill=theme.secondary_text, font_size_px=15),
            anchor="start",
        ),
    ]
    primitives.extend(_stack_primitives(stack, output_spec, theme))
    primitives.extend(_point_stack_notes(scene, output_spec, theme))
    return DrawingScene(
        id=scene.scene_id,
        role="point_stack_schematic",
        canvas=canvas,
        coordinate_frame=CoordinateFrame(None, "down", scene.visual_units),
        primitives=tuple(primitives),
        metadata={"render_mode_id": scene.render_mode_id, "theme_id": theme.theme_id},
    )


def _point_stack_shapes(scene: CrossSectionSceneModel) -> tuple[MaterialShape, ...]:
    physical = scene.coordinate_frame.get("physical_bounds", (0.0, 0.0, 1.0, 1.0))
    left, _, right, _ = _bounds_tuple(physical)
    center_x = (left + right) / 2.0
    containing = [
        shape
        for shape in scene.material_shapes
        if shape.physical_bounds[0] <= center_x <= shape.physical_bounds[2]
    ]
    shapes = containing or list(scene.material_shapes)
    return tuple(sorted(shapes, key=lambda item: item.physical_bounds[3], reverse=True))


def _bounds_tuple(value: object) -> tuple[float, float, float, float]:
    if not isinstance(value, (list, tuple)) or len(value) != 4:
        return (0.0, 0.0, 1.0, 1.0)
    return (float(value[0]), float(value[1]), float(value[2]), float(value[3]))


def _stack_primitives(
    stack: tuple[MaterialShape, ...],
    output_spec: CrossSectionOutputSpec,
    theme: RenderTheme,
) -> list[DrawingPrimitive]:
    if not stack:
        return []
    total = sum(_shape_thickness(shape) for shape in stack) or 1.0
    x = 92.0
    y = 126.0
    width = 260.0
    max_height = output_spec.height_px - 210.0
    primitives: list[DrawingPrimitive] = []
    for shape in stack[:16]:
        height = max(28.0, max_height * _shape_thickness(shape) / total)
        fill = shape.visual_style.get("fill", "#64748b")
        primitives.extend(_stack_row_primitives(shape, x, y, width, height, fill, theme))
        y += height
    return primitives


def _stack_row_primitives(
    shape: MaterialShape,
    x: float,
    y: float,
    width: float,
    height: float,
    fill: str,
    theme: RenderTheme,
) -> tuple[DrawingPrimitive, ...]:
    text_color = contrast_text_for_fill(fill, theme)
    return (
        RectangleMark(
            x,
            y,
            width,
            height,
            DrawingStyle(stroke=theme.material_stroke, fill=fill, stroke_width=1.2),
            shape.material_id,
        ),
        TextMark(
            CanvasPoint(x + width + 28.0, y + min(height - 8.0, 20.0)),
            f"{shape.material_name}  {format_length(_shape_thickness(shape), 'um')}",
            DrawingStyle(stroke=theme.primary_text, fill=theme.primary_text, font_size_px=16),
            anchor="start",
        ),
        TextMark(
            CanvasPoint(x + 12.0, y + min(height - 8.0, 20.0)),
            shape.material_id,
            DrawingStyle(stroke=text_color, fill=text_color, font_size_px=13),
            anchor="start",
        ),
    )


def _point_stack_notes(
    scene: CrossSectionSceneModel,
    output_spec: CrossSectionOutputSpec,
    theme: RenderTheme,
) -> list[DrawingPrimitive]:
    notes = tuple(dict.fromkeys(scene.warnings + ("Lateral geometry hidden for point-stack view",)))
    return [
        TextMark(
            CanvasPoint(64.0, output_spec.height_px - 52.0 + index * 18.0),
            note,
            DrawingStyle(stroke=theme.secondary_text, fill=theme.secondary_text, font_size_px=14),
            anchor="start",
        )
        for index, note in enumerate(notes[:2])
    ]


def _shape_thickness(shape: MaterialShape) -> float:
    return abs(shape.physical_bounds[3] - shape.physical_bounds[1])
