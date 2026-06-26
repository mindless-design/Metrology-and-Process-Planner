"""Build editable drawing scenes for captured layout image annotations."""

from __future__ import annotations

from dataclasses import replace
from typing import Optional

from metrology_process_planner.domains.measurement.records import MeasurementRecord
from metrology_process_planner.domains.session import ArtifactRecord, CaptureRecord
from metrology_process_planner.rendering.annotation_features import feature_primitives
from metrology_process_planner.rendering.coordinates import CanvasTransform
from metrology_process_planner.rendering.primitives import (
    CanvasPoint,
    DrawingPrimitive,
    EllipseMark,
    LineMark,
    RectangleMark,
    TextMark,
)
from metrology_process_planner.rendering.scene import (
    CanvasSpec,
    CoordinateFrame,
    DrawingScene,
    ImageLayer,
)
from metrology_process_planner.rendering.styles import DrawingStyle
from metrology_process_planner.rendering.theme import render_theme

DEFAULT_CANVAS_WIDTH = 1024
DEFAULT_CANVAS_HEIGHT = 768
THEME = render_theme("engineering_dark")


def build_layout_annotation_scene(
    capture: CaptureRecord,
    base_image: Optional[ArtifactRecord] = None,
    scene_id: Optional[str] = None,
) -> DrawingScene:
    """Build an editable annotation scene for a layout capture."""

    if capture.geometry.bounds is None:
        raise ValueError("Layout annotation scenes require capture bounds.")
    canvas = _canvas_for_image(base_image)
    transform = CanvasTransform(capture.geometry.bounds, canvas)
    primitives: list[DrawingPrimitive] = [_capture_border(canvas)]
    for feature in capture.geometry.features:
        primitives.extend(feature_primitives(transform, feature))
    for measurement in capture.measurements:
        primitives.extend(_measurement_primitives(transform, measurement))
    return DrawingScene(
        id=scene_id or f"{capture.id}-layout-annotation",
        role="layout_annotation",
        canvas=canvas,
        coordinate_frame=CoordinateFrame(source_bounds=capture.geometry.bounds, y_axis="down"),
        image_layers=() if base_image is None else (_image_layer(base_image, canvas),),
        primitives=tuple(primitives),
        metadata={"capture_id": capture.id},
    )


def build_measurement_annotation_scene(
    capture: CaptureRecord,
    measurement: MeasurementRecord,
    base_image: Optional[ArtifactRecord] = None,
    scene_id: Optional[str] = None,
) -> DrawingScene:
    """Build an editable annotation scene for one child measurement."""

    scoped = replace(capture, measurements=(measurement,))
    scene = build_layout_annotation_scene(
        scoped,
        base_image=base_image,
        scene_id=scene_id or f"{measurement.id}-measurement-annotation",
    )
    metadata = {**dict(scene.metadata or {}), "measurement_id": measurement.id}
    return replace(scene, role="measurement_annotation", metadata=metadata)


def _canvas_for_image(image: Optional[ArtifactRecord]) -> CanvasSpec:
    width = image.file.width_px if image is not None else DEFAULT_CANVAS_WIDTH
    height = image.file.height_px if image is not None else DEFAULT_CANVAS_HEIGHT
    return CanvasSpec(
        width_px=width or DEFAULT_CANVAS_WIDTH,
        height_px=height or DEFAULT_CANVAS_HEIGHT,
        background=THEME.background,
    )


def _image_layer(image: ArtifactRecord, canvas: CanvasSpec) -> ImageLayer:
    return ImageLayer(
        path=image.relative_path,
        width_px=image.file.width_px or canvas.width_px,
        height_px=image.file.height_px or canvas.height_px,
        opacity=0.86,
    )


def _capture_border(canvas: CanvasSpec) -> RectangleMark:
    return RectangleMark(
        x=0,
        y=0,
        width=canvas.width_px,
        height=canvas.height_px,
        style=DrawingStyle(stroke=THEME.panel_stroke, fill=None, stroke_width=2.0, opacity=0.75),
        label="capture bounds",
    )


def _measurement_primitives(
    transform: CanvasTransform,
    measurement: MeasurementRecord,
) -> list[DrawingPrimitive]:
    start = transform.map_point(measurement.start)
    end = transform.map_point(measurement.end)
    style = DrawingStyle(
        stroke=measurement.annotation_color,
        fill=None,
        stroke_width=max(3.0, measurement.line_weight),
        font_size_px=16,
    )
    return [
        LineMark(start=start, end=end, style=style, label=measurement.label, end_marker="arrow"),
        _endpoint_circle(start, style, "start"),
        _endpoint_circle(end, style, "end"),
        _measurement_label(start, end, measurement.label, style),
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


def _measurement_label(
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
