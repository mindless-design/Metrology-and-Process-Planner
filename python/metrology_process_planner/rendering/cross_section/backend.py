"""Replaceable renderer backend contracts for cross-section scenes."""

from __future__ import annotations

from pathlib import Path
from typing import Optional, Protocol

from metrology_process_planner.domains.geometry import Box
from metrology_process_planner.rendering.coordinates import CanvasTransform
from metrology_process_planner.rendering.cross_section.models import (
    CrossSectionOutputSpec,
    CrossSectionRenderResult,
)
from metrology_process_planner.rendering.cross_section.point_stack_scene import (
    point_stack_drawing_scene,
)
from metrology_process_planner.rendering.cross_section.scene_models import CrossSectionSceneModel
from metrology_process_planner.rendering.cross_section.themed_primitives import (
    canvas_overlays,
    label_backdrop,
    leader,
    rectangle,
    text,
)
from metrology_process_planner.rendering.export import DrawingExporter, SvgRasterizer
from metrology_process_planner.rendering.primitives import (
    CanvasPoint,
    DrawingPrimitive,
    TextMark,
)
from metrology_process_planner.rendering.scene import CanvasSpec, CoordinateFrame, DrawingScene
from metrology_process_planner.rendering.styles import DrawingStyle
from metrology_process_planner.rendering.theme import render_theme


class CrossSectionRenderer(Protocol):
    """Backend contract for rendering cross-section scenes."""

    def render(
        self,
        scene: CrossSectionSceneModel,
        output_spec: CrossSectionOutputSpec,
    ) -> CrossSectionRenderResult:
        """Render a scene to one or more output artifacts."""


class SvgCrossSectionRenderer:
    """Render cross-section scenes through the existing SVG drawing backend."""

    def __init__(self, rasterizer: Optional[SvgRasterizer] = None) -> None:
        self._rasterizer = rasterizer

    def render(
        self,
        scene: CrossSectionSceneModel,
        output_spec: CrossSectionOutputSpec,
    ) -> CrossSectionRenderResult:
        """Render a scene to SVG and optionally PNG when output path ends in .png."""

        output_path = (
            Path(output_spec.output_path) if output_spec.output_path else Path("preview.svg")
        )
        svg_path = output_path.with_suffix(".svg")
        spec_path = output_path.with_suffix(".json")
        png_path = output_path if output_path.suffix.lower() == ".png" else None
        drawing = scene_to_drawing_scene(scene, output_spec)
        result = DrawingExporter().export(drawing, spec_path, svg_path, png_path, self._rasterizer)
        warnings = scene.warnings + result.warnings
        path = str(result.png_path or result.svg_path)
        status = "warning" if warnings else "success"
        return CrossSectionRenderResult(
            output_spec.artifact_id,
            path,
            result.width_px,
            result.height_px,
            status,
            warnings,
            {
                "render_mode_id": scene.render_mode_id,
                "theme_id": output_spec.theme_id,
                "background_color": render_theme(output_spec.theme_id).background,
                "compression_metadata": scene.compression_metadata.__dict__,
                "label_layout_warnings": tuple(
                    item for item in scene.warnings if item.startswith("RENDER_LABEL")
                ),
            },
        )


def scene_to_drawing_scene(
    scene: CrossSectionSceneModel,
    output_spec: CrossSectionOutputSpec,
) -> DrawingScene:
    """Adapt a backend-independent cross-section scene to editable drawing primitives."""

    theme = render_theme(output_spec.theme_id)
    if scene.render_mode_id == "point_stack_schematic":
        return point_stack_drawing_scene(scene, output_spec, theme)
    canvas = CanvasSpec(output_spec.width_px, output_spec.height_px, background=theme.background)
    bounds = _source_bounds(scene)
    transform = CanvasTransform(bounds, canvas)
    primitives: list[DrawingPrimitive] = []
    for shape in scene.material_shapes:
        primitives.append(rectangle(shape.visual_bounds, transform, shape.visual_style, theme))
    for label in scene.labels:
        if label.placement_type != "legend_only":
            primitives.append(label_backdrop(label.bounding_box, transform, theme))
        primitives.append(text(label.position, label.text, transform, theme))
        if label.leader_line:
            primitives.append(leader(label.leader_line, transform, theme))
    primitives.extend(canvas_overlays(scene, output_spec, theme))
    if scene.title:
        primitives.append(
            TextMark(
                CanvasPoint(output_spec.width_px / 2.0, 24.0),
                scene.title,
                DrawingStyle(
                    stroke=theme.primary_text,
                    fill=theme.primary_text,
                    font_size_px=theme.title_size_px,
                ),
            )
        )
    return DrawingScene(
        id=scene.scene_id,
        role="cross_section",
        canvas=canvas,
        coordinate_frame=CoordinateFrame(bounds, "down", scene.visual_units),
        primitives=tuple(primitives),
        metadata={"render_mode_id": scene.render_mode_id, "theme_id": theme.theme_id},
    )


def _source_bounds(scene: CrossSectionSceneModel) -> Box:
    left, bottom, right, top = _visual_bounds(
        scene.coordinate_frame.get("visual_bounds", (0.0, 0.0, 1.0, 1.0))
    )
    for label in scene.labels:
        if label.placement_type == "legend_only":
            continue
        label_left, label_bottom, label_right, label_top = _label_bounds(label.bounding_box)
        left = min(left, label_left, label.anchor_point[0])
        bottom = min(bottom, label_bottom, label.anchor_point[1])
        right = max(right, label_right, label.anchor_point[0])
        top = max(top, label_top, label.anchor_point[1])
        if label.leader_line:
            for point in label.leader_line:
                left = min(left, point[0])
                bottom = min(bottom, point[1])
                right = max(right, point[0])
                top = max(top, point[1])
    width = max(1.0, right - left)
    height = max(1.0, top - bottom)
    return Box(
        left - width * 0.05,
        bottom - height * 0.08,
        right + width * 0.35,
        top + height * 0.12,
    )


def _visual_bounds(value: object) -> tuple[float, float, float, float]:
    if not isinstance(value, (list, tuple)) or len(value) != 4:
        return (0.0, 0.0, 1.0, 1.0)
    return (float(value[0]), float(value[1]), float(value[2]), float(value[3]))


def _label_bounds(value: tuple[float, float, float, float]) -> tuple[float, float, float, float]:
    x, y, width, height = value
    return (x, y, x + width, y + height)
