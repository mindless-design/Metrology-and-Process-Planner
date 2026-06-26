"""Render specifications, editable scenes, planners, and export contracts."""

from metrology_process_planner.rendering.annotation_planner import (
    build_layout_annotation_scene,
    build_measurement_annotation_scene,
)
from metrology_process_planner.rendering.coordinates import CanvasTransform
from metrology_process_planner.rendering.cross_section import (
    CompressionMetadata,
    CompressionPolicy,
    CrossSectionOutputSpec,
    CrossSectionRenderResult,
    CrossSectionSceneModel,
    FeatureFilter,
    LabelPolicy,
    RenderIntent,
    RenderProfile,
    SvgCrossSectionRenderer,
    ThinLayerPolicy,
    VisualTransform,
    build_cross_section_scene,
    build_process_flow_scenes,
    build_render_artifact_record,
    build_render_projection,
    built_in_render_profile,
    built_in_render_profiles,
)
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
from metrology_process_planner.rendering.theme import RenderTheme, render_theme

__all__ = [
    "AnnotationSpec",
    "CanvasPoint",
    "CanvasSpec",
    "CanvasTransform",
    "CompressionMetadata",
    "CompressionPolicy",
    "CoordinateFrame",
    "CrossSectionOutputSpec",
    "CrossSectionRenderResult",
    "CrossSectionScene",
    "CrossSectionSceneModel",
    "DrawingExporter",
    "DrawingExportResult",
    "DrawingPrimitive",
    "DrawingScene",
    "DrawingStyle",
    "EllipseMark",
    "FeatureFilter",
    "ImageExportResult",
    "ImageLayer",
    "LabelPolicy",
    "LegendModel",
    "LineMark",
    "MeasurementAnnotation",
    "PolygonMark",
    "PolylineMark",
    "PreviewSpec",
    "RectangleMark",
    "RenderSpec",
    "RenderIntent",
    "RenderProfile",
    "RenderTheme",
    "SvgRasterizer",
    "SvgCrossSectionRenderer",
    "TextMark",
    "ThinLayerPolicy",
    "VisualTransform",
    "build_cross_section_drawing_scene",
    "build_cross_section_scene",
    "build_layout_annotation_scene",
    "build_measurement_annotation_scene",
    "build_process_flow_scenes",
    "build_render_artifact_record",
    "build_render_projection",
    "built_in_render_profile",
    "built_in_render_profiles",
    "render_scene_to_svg",
    "render_theme",
    "scene_from_dict",
    "scene_to_dict",
]
