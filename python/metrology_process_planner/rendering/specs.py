"""Structured render and annotation models."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Optional

from metrology_process_planner.domains.geometry import Box, Point
from metrology_process_planner.domains.process import CrossSectionProfile


@dataclass(frozen=True)
class AnnotationSpec:
    """Style and label settings for a visual annotation."""

    label: str
    color: str = "#ffcc00"
    line_weight: float = 2.0
    text_scale: float = 1.0


@dataclass(frozen=True)
class MeasurementAnnotation:
    """Rendered annotation tied to a measurement line."""

    label: str
    start: Point
    end: Point
    annotation: AnnotationSpec


@dataclass(frozen=True)
class PreviewSpec:
    """Preview rendering request constrained for an interactive UI."""

    bounds: Box
    max_width_px: int = 1024
    max_height_px: int = 768


@dataclass(frozen=True)
class RenderSpec:
    """Image rendering request for saved or exported artifacts."""

    bounds: Box
    dpi: int = 150
    annotations: tuple[MeasurementAnnotation, ...] = ()


@dataclass(frozen=True)
class LegendModel:
    """Legend entries as material or annotation labels and colors."""

    entries: tuple[tuple[str, str], ...]


@dataclass(frozen=True)
class CrossSectionScene:
    """Structured cross-section scene ready for a concrete renderer."""

    profile: CrossSectionProfile
    title: str
    legend: Optional[LegendModel] = None
    annotations: tuple[AnnotationSpec, ...] = ()


@dataclass(frozen=True)
class ImageExportResult:
    """Result metadata from a raster image export."""

    path: str
    width_px: int
    height_px: int
    warnings: tuple[str, ...] = ()
