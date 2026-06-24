"""Render specifications, editable scenes, planners, and export contracts."""

from metrology_process_planner.rendering.annotation_planner import (
    build_layout_annotation_scene,
    build_measurement_annotation_scene,
)
from metrology_process_planner.rendering.coordinates import CanvasTransform
from metrology_process_planner.rendering.cross_section_planner import (
    build_cross_section_drawing_scene,
)
from metrology_process_planner.rendering.export import (
    DrawingExporter,
    DrawingExportResult,
    SvgRasterizer,
)
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
from metrology_process_planner.rendering.scene import (
    CanvasSpec,
    CoordinateFrame,
    DrawingScene,
    ImageLayer,
    scene_from_dict,
    scene_to_dict,
)
from metrology_process_planner.rendering.specs import (
    AnnotationSpec,
    CrossSectionScene,
    ImageExportResult,
    LegendModel,
    MeasurementAnnotation,
    PreviewSpec,
    RenderSpec,
)
from metrology_process_planner.rendering.styles import DrawingStyle
from metrology_process_planner.rendering.svg_renderer import render_scene_to_svg

__all__ = [
    "AnnotationSpec",
    "CanvasPoint",
    "CanvasSpec",
    "CanvasTransform",
    "CoordinateFrame",
    "CrossSectionScene",
    "DrawingExporter",
    "DrawingExportResult",
    "DrawingPrimitive",
    "DrawingScene",
    "DrawingStyle",
    "EllipseMark",
    "ImageExportResult",
    "ImageLayer",
    "LegendModel",
    "LineMark",
    "MeasurementAnnotation",
    "PolygonMark",
    "PolylineMark",
    "PreviewSpec",
    "RectangleMark",
    "RenderSpec",
    "SvgRasterizer",
    "TextMark",
    "build_cross_section_drawing_scene",
    "build_layout_annotation_scene",
    "build_measurement_annotation_scene",
    "render_scene_to_svg",
    "scene_from_dict",
    "scene_to_dict",
]
