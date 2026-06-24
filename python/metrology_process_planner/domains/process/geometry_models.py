"""Geometry data models for process solver snapshots and projections."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class MaterialInterval:
    """A vertical material interval in one stack column."""

    material_id: str
    z_min: float
    z_max: float


@dataclass(frozen=True)
class StackColumn:
    """A sampled x-position and its vertical material stack."""

    x: float
    intervals: tuple[MaterialInterval, ...]

    @property
    def top(self) -> float:
        """Return the column top height."""

        if not self.intervals:
            return 0.0
        return max(interval.z_max for interval in self.intervals)


@dataclass(frozen=True)
class SurfaceProfile:
    """Top surface heights over sampled x positions."""

    points: tuple[tuple[float, float], ...]


@dataclass(frozen=True)
class MaterialRegion:
    """Render-ready rectangular material region."""

    material_id: str
    x_min: float
    x_max: float
    z_min: float
    z_max: float


@dataclass(frozen=True)
class StackGeometry2D:
    """Sampled 2D stack geometry used by the hybrid solver."""

    columns: tuple[StackColumn, ...]
    regions: tuple[MaterialRegion, ...] = ()

    @property
    def surface(self) -> SurfaceProfile:
        """Return top surface profile for the sampled geometry."""

        return SurfaceProfile(tuple((column.x, column.top) for column in self.columns))


@dataclass(frozen=True)
class GeometrySnapshot:
    """Geometry after one solver operation."""

    step_id: str
    geometry: StackGeometry2D
    signature: str
    metadata: dict[str, str]


@dataclass(frozen=True)
class MaskInterval:
    """One one-dimensional mask opening interval."""

    x_min: float
    x_max: float

    def contains(self, x: float) -> bool:
        """Return whether x falls inside the interval."""

        return self.x_min <= x <= self.x_max

    @property
    def width(self) -> float:
        """Return interval width."""

        return max(0.0, self.x_max - self.x_min)


@dataclass(frozen=True)
class PointSample:
    """Point stack extraction result."""

    x: float
    intervals: tuple[MaterialInterval, ...]


@dataclass(frozen=True)
class CutlineSample:
    """Cutline cross-section extraction result."""

    x: float
    intervals: tuple[MaterialInterval, ...]


@dataclass(frozen=True)
class RenderProjection:
    """Render-ready solver output projection."""

    regions: tuple[MaterialRegion, ...]
    surface: SurfaceProfile
    material_order: tuple[str, ...]


@dataclass(frozen=True)
class CrossSectionProfile:
    """A set of sampled stack columns for cross-section rendering."""

    columns: tuple[StackColumn, ...]
