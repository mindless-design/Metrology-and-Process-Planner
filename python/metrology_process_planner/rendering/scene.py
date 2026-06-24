"""Editable drawing scene contracts and JSON serialization."""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
from typing import Any, Optional

from metrology_process_planner.domains.geometry import Box
from metrology_process_planner.rendering.primitive_io import (
    primitive_from_dict,
    primitive_to_dict,
)
from metrology_process_planner.rendering.primitives import (
    DrawingPrimitive,
)


@dataclass(frozen=True)
class CanvasSpec:
    """Canvas dimensions and background color for a drawing scene."""

    width_px: int
    height_px: int
    background: str = "#ffffff"


@dataclass(frozen=True)
class CoordinateFrame:
    """Source coordinate metadata used to regenerate mapped primitives."""

    source_bounds: Optional[Box] = None
    y_axis: str = "down"
    units: str = ""


@dataclass(frozen=True)
class ImageLayer:
    """A raster or vector image layer placed under drawing primitives."""

    path: str
    width_px: int
    height_px: int
    opacity: float = 1.0


@dataclass(frozen=True)
class DrawingScene:
    """An editable vector scene for annotations or generated schematics."""

    id: str
    role: str
    canvas: CanvasSpec
    coordinate_frame: CoordinateFrame = CoordinateFrame()
    image_layers: tuple[ImageLayer, ...] = ()
    primitives: tuple[DrawingPrimitive, ...] = ()
    metadata: Optional[Mapping[str, Any]] = None

    def __post_init__(self) -> None:
        if self.metadata is None:
            object.__setattr__(self, "metadata", {})


def scene_to_dict(scene: DrawingScene) -> dict[str, Any]:
    """Serialize a drawing scene to JSON-compatible data."""

    return {
        "id": scene.id,
        "role": scene.role,
        "canvas": _canvas_to_dict(scene.canvas),
        "coordinate_frame": _frame_to_dict(scene.coordinate_frame),
        "image_layers": [_layer_to_dict(layer) for layer in scene.image_layers],
        "primitives": [primitive_to_dict(mark) for mark in scene.primitives],
        "metadata": dict(scene.metadata or {}),
    }


def scene_from_dict(data: Mapping[str, Any]) -> DrawingScene:
    """Build a drawing scene from JSON-compatible data."""

    return DrawingScene(
        id=str(data["id"]),
        role=str(data["role"]),
        canvas=_canvas_from_dict(data["canvas"]),
        coordinate_frame=_frame_from_dict(data.get("coordinate_frame", {})),
        image_layers=tuple(_layer_from_dict(item) for item in data.get("image_layers", ())),
        primitives=tuple(primitive_from_dict(item) for item in data.get("primitives", ())),
        metadata=dict(data.get("metadata", {})),
    )


def _canvas_to_dict(canvas: CanvasSpec) -> dict[str, Any]:
    return {
        "width_px": canvas.width_px,
        "height_px": canvas.height_px,
        "background": canvas.background,
    }


def _canvas_from_dict(data: Mapping[str, Any]) -> CanvasSpec:
    return CanvasSpec(
        width_px=int(data["width_px"]),
        height_px=int(data["height_px"]),
        background=str(data.get("background", "#ffffff")),
    )


def _frame_to_dict(frame: CoordinateFrame) -> dict[str, Any]:
    return {
        "source_bounds": None if frame.source_bounds is None else frame.source_bounds.to_dict(),
        "y_axis": frame.y_axis,
        "units": frame.units,
    }


def _frame_from_dict(data: Mapping[str, Any]) -> CoordinateFrame:
    source = data.get("source_bounds")
    return CoordinateFrame(
        source_bounds=None if source is None else Box.from_dict(source),
        y_axis=str(data.get("y_axis", "down")),
        units=str(data.get("units", "")),
    )


def _layer_to_dict(layer: ImageLayer) -> dict[str, Any]:
    return {
        "path": layer.path,
        "width_px": layer.width_px,
        "height_px": layer.height_px,
        "opacity": layer.opacity,
    }


def _layer_from_dict(data: Mapping[str, Any]) -> ImageLayer:
    return ImageLayer(
        path=str(data["path"]),
        width_px=int(data["width_px"]),
        height_px=int(data["height_px"]),
        opacity=float(data.get("opacity", 1.0)),
    )
