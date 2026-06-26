"""Geometry data models for process solver snapshots and projections."""

from __future__ import annotations

from dataclasses import dataclass

from metrology_process_planner.solver.advanced_geometry_models import (
    ConformalLayerMetadata,
    PinchOffRegion,
    SeamRegion,
    TaperedRegion,
    UndercutRegion,
    VoidRegion,
)


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
    void_regions: tuple[VoidRegion, ...] = ()
    seam_regions: tuple[SeamRegion, ...] = ()
    pinch_off_regions: tuple[PinchOffRegion, ...] = ()
    undercut_regions: tuple[UndercutRegion, ...] = ()
    tapered_regions: tuple[TaperedRegion, ...] = ()
    conformal_layers: tuple[ConformalLayerMetadata, ...] = ()

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
    projection_id: str = "projection:final"
    projection_type: str = "physical_cross_section"
    source_solver_result_id: str = ""
    source_step_id: str = ""
    source_capture_id: str = ""
    materials: tuple[dict[str, object], ...] = ()
    physical_bounds: tuple[float, float, float, float] | None = None
    units: str = "um"
    hidden_material_ids: tuple[str, ...] = ()
    label_candidates: tuple[dict[str, object], ...] = ()
    changed_regions: tuple[MaterialRegion, ...] = ()
    material_regions: tuple[MaterialRegion, ...] = ()
    surface_profiles: tuple[SurfaceProfile, ...] = ()
    void_regions: tuple[VoidRegion, ...] = ()
    seam_regions: tuple[SeamRegion, ...] = ()
    pinch_off_regions: tuple[PinchOffRegion, ...] = ()
    undercut_regions: tuple[UndercutRegion, ...] = ()
    tapered_regions: tuple[TaperedRegion, ...] = ()
    conformal_layers: tuple[ConformalLayerMetadata, ...] = ()
    warnings: tuple[str, ...] = ()
    compression_hints: dict[str, object] | None = None
    thin_layer_hints: dict[str, object] | None = None
    approximation_notes: tuple[str, ...] = ()

    def __post_init__(self) -> None:
        if self.compression_hints is None:
            object.__setattr__(self, "compression_hints", {})
        if self.thin_layer_hints is None:
            object.__setattr__(self, "thin_layer_hints", {})
        if not self.material_regions:
            object.__setattr__(self, "material_regions", self.regions)
        if not self.surface_profiles:
            object.__setattr__(self, "surface_profiles", (self.surface,))


@dataclass(frozen=True)
class CrossSectionProfile:
    """A set of sampled stack columns for cross-section rendering."""

    columns: tuple[StackColumn, ...]
