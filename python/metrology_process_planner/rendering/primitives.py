"""Typed drawing primitives used by editable render scenes."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Union

from metrology_process_planner.rendering.styles import DrawingStyle


@dataclass(frozen=True)
class CanvasPoint:
    """A point in rendered canvas pixel coordinates."""

    x: float
    y: float


@dataclass(frozen=True)
class LineMark:
    """A line, measurement, or arrow primitive."""

    start: CanvasPoint
    end: CanvasPoint
    style: DrawingStyle
    label: str = ""
    start_marker: str = ""
    end_marker: str = ""


@dataclass(frozen=True)
class RectangleMark:
    """An axis-aligned rectangle primitive."""

    x: float
    y: float
    width: float
    height: float
    style: DrawingStyle
    label: str = ""


@dataclass(frozen=True)
class EllipseMark:
    """An ellipse or circle primitive."""

    center: CanvasPoint
    radius_x: float
    radius_y: float
    style: DrawingStyle
    label: str = ""


@dataclass(frozen=True)
class PolylineMark:
    """An open connected path primitive."""

    points: tuple[CanvasPoint, ...]
    style: DrawingStyle
    label: str = ""


@dataclass(frozen=True)
class PolygonMark:
    """A closed filled or stroked polygon primitive."""

    points: tuple[CanvasPoint, ...]
    style: DrawingStyle
    label: str = ""


@dataclass(frozen=True)
class TextMark:
    """A text label primitive."""

    position: CanvasPoint
    text: str
    style: DrawingStyle
    anchor: str = "middle"


DrawingPrimitive = Union[
    LineMark,
    RectangleMark,
    EllipseMark,
    PolylineMark,
    PolygonMark,
    TextMark,
]
