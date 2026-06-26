"""Synthetic process fixture models and paths."""

from __future__ import annotations

from dataclasses import asdict, dataclass
from pathlib import Path

FIXTURE_ROOT = Path(__file__).resolve().parent / "fixtures"
GDS_ROOT = FIXTURE_ROOT / "gds"
RECIPE_ROOT = FIXTURE_ROOT / "recipes"
SESSION_ROOT = FIXTURE_ROOT / "synthetic_sessions"
GOLDEN_ROOT = Path(__file__).resolve().parent / "golden"
OUTPUT_ROOT = Path(__file__).resolve().parent / "output"


@dataclass(frozen=True)
class GeometryExtractionWarning:
    """Warning produced while extracting synthetic layout geometry."""

    code: str
    message: str
    layer_name: str = ""


@dataclass(frozen=True)
class ExtractedRect:
    """One rectangle from the synthetic geometry manifest."""

    structure: str
    layer_name: str
    name: str
    x_min: float
    y_min: float
    x_max: float
    y_max: float

    def intersects_roi(self, roi: tuple[float, float, float, float]) -> bool:
        """Return whether this rectangle intersects an ROI."""

        x_min, y_min, x_max, y_max = roi
        return (
            self.x_min < x_max
            and self.x_max > x_min
            and self.y_min < y_max
            and self.y_max > y_min
        )

    def contains_point(self, x: float, y: float) -> bool:
        """Return whether the point falls inside the rectangle."""

        return self.x_min <= x <= self.x_max and self.y_min <= y <= self.y_max

    def crosses_y(self, y: float) -> bool:
        """Return whether a horizontal cutline crosses the rectangle."""

        return self.y_min <= y <= self.y_max


@dataclass(frozen=True)
class GeometrySnapshot:
    """Deterministic geometry extraction result."""

    structure: str
    rectangles: tuple[ExtractedRect, ...]
    warnings: tuple[GeometryExtractionWarning, ...] = ()

    def layer_names(self) -> tuple[str, ...]:
        """Return sorted layer names in this snapshot."""

        return tuple(sorted({rect.layer_name for rect in self.rectangles}))

    def to_dict(self) -> dict[str, object]:
        """Serialize a geometry snapshot."""

        return {
            "structure": self.structure,
            "layers": list(self.layer_names()),
            "rectangles": [asdict(rect) for rect in self.rectangles],
            "warnings": [asdict(warning) for warning in self.warnings],
        }


@dataclass(frozen=True)
class MaskInterval:
    """One mask interval from a horizontal cutline."""

    layer_name: str
    x_min: float
    x_max: float
    source_rect: str


@dataclass(frozen=True)
class CutlineSample:
    """Horizontal cutline extraction."""

    structure: str
    y: float
    intervals: tuple[MaskInterval, ...]


@dataclass(frozen=True)
class PointSample:
    """Point membership extraction."""

    x: float
    y: float
    layers: tuple[str, ...]
    rectangles: tuple[str, ...]
