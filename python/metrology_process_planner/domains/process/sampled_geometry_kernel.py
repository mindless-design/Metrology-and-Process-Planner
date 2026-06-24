"""Sampled-column geometry backend for the hybrid process solver."""

from __future__ import annotations

import hashlib

from metrology_process_planner.domains.process.geometry_models import (
    CutlineSample,
    MaskInterval,
    MaterialInterval,
    PointSample,
    RenderProjection,
    StackGeometry2D,
)
from metrology_process_planner.domains.process.sampled_geometry_helpers import (
    _add_top,
    _clean,
    _clip_column,
    _etch_column,
    _grow_conformal_column,
    _is_masked,
    _laterally_attacked_xs,
    _make_column,
    _make_samples,
    _map_columns,
    _material_density,
    _material_order,
    _median_top,
    _regions,
)
from metrology_process_planner.domains.process.solver_profiles import (
    ConformalProfile,
    EtchProfile,
    PlanarizationProfile,
)
from metrology_process_planner.domains.process.steps import MaskPolarity


class SampledGeometryKernel:
    """Useful v1 geometry backend based on sampled material stacks."""

    def __init__(self, x_min: float = 0.0, x_max: float = 10.0, sample_count: int = 201) -> None:
        self.xs = _make_samples(x_min, x_max, sample_count)

    def initialize_substrate(self, material_id: str, thickness: float) -> StackGeometry2D:
        """Create a flat substrate stack across the sampled x range."""

        columns = tuple(
            _make_column(x, MaterialInterval(material_id, 0.0, thickness))
            for x in self.xs
        )
        return StackGeometry2D(columns)

    def deposit_blanket(
        self,
        geometry: StackGeometry2D,
        material_id: str,
        thickness: float,
    ) -> StackGeometry2D:
        """Deposit a topography-following film on every sampled column."""

        return _map_columns(geometry, lambda column: _add_top(column, material_id, thickness))

    def deposit_patterned(
        self,
        geometry: StackGeometry2D,
        material_id: str,
        thickness: float,
        mask: tuple[MaskInterval, ...],
        polarity: MaskPolarity,
    ) -> StackGeometry2D:
        """Deposit a film in direct or inverted mask intervals."""

        return _map_columns(
            geometry,
            lambda column: _add_top(column, material_id, thickness)
            if _is_masked(column.x, mask, polarity)
            else column,
        )

    def deposit_conformal(
        self,
        geometry: StackGeometry2D,
        material_id: str,
        thickness: float,
        profile: ConformalProfile,
    ) -> StackGeometry2D:
        """Approximate exposed-surface growth with top and sidewall coverage."""

        grown = [list(column.intervals) for column in geometry.columns]
        for index, _ in enumerate(geometry.columns):
            _grow_conformal_column(grown, geometry, index, material_id, thickness, profile)
        columns = tuple(
            _make_column(column.x, *_clean(tuple(grown[index])))
            for index, column in enumerate(geometry.columns)
        )
        return StackGeometry2D(columns)

    def etch_directional(self, geometry: StackGeometry2D, profile: EtchProfile) -> StackGeometry2D:
        """Remove target materials top-down until depth or blocker is reached."""

        depth = profile.depth * profile.overetch_factor
        return _map_columns(geometry, lambda column: _etch_column(column, profile, depth))

    def etch_isotropic(self, geometry: StackGeometry2D, profile: EtchProfile) -> StackGeometry2D:
        """Approximate isotropic exposed-boundary etch with lateral attack."""

        radius = profile.lateral_attack or profile.depth
        attacked = _laterally_attacked_xs(geometry, radius)
        return _map_columns(
            geometry,
            lambda column: _etch_column(column, profile, profile.depth)
            if column.x in attacked
            else column,
        )

    def etch_tapered(self, geometry: StackGeometry2D, profile: EtchProfile) -> StackGeometry2D:
        """Approximate tapered etch using the target etch depth."""

        depth = profile.depth * profile.overetch_factor
        return _map_columns(geometry, lambda column: _etch_column(column, profile, depth))

    def planarize(
        self,
        geometry: StackGeometry2D,
        profile: PlanarizationProfile,
    ) -> StackGeometry2D:
        """Clip all stacks to an ideal planar target height."""

        target = profile.target_height
        if target is None:
            target = _median_top(geometry)
        return _map_columns(geometry, lambda column: _clip_column(column, target))

    def cmp_planarize(
        self,
        geometry: StackGeometry2D,
        profile: PlanarizationProfile,
    ) -> StackGeometry2D:
        """Apply explicit heuristic CMP overpolish, dishing, and erosion."""

        base = profile.target_height if profile.target_height is not None else _median_top(geometry)
        density = _material_density(geometry, profile.stop_materials)
        target = base - profile.overpolish - profile.dishing_coefficient * density
        target -= profile.erosion_coefficient * (1.0 - density)
        return _map_columns(geometry, lambda column: _clip_column(column, target))

    def extract_point_stack(self, geometry: StackGeometry2D, x: float) -> PointSample:
        """Extract the nearest sampled material stack at x."""

        column = min(geometry.columns, key=lambda item: abs(item.x - x))
        return PointSample(column.x, column.intervals)

    def extract_cutline_profile(
        self,
        geometry: StackGeometry2D,
        x_min: float,
        x_max: float,
    ) -> tuple[CutlineSample, ...]:
        """Extract sampled material stacks inside a cutline window."""

        return tuple(
            CutlineSample(column.x, column.intervals)
            for column in geometry.columns
            if x_min <= column.x <= x_max
        )

    def make_render_projection(self, geometry: StackGeometry2D) -> RenderProjection:
        """Build render-ready material regions and surface points."""

        return RenderProjection(_regions(geometry), geometry.surface, _material_order(geometry))

    def compute_signature(self, geometry: StackGeometry2D) -> str:
        """Compute a deterministic signature for the sampled geometry."""

        text = repr(tuple((c.x, c.intervals) for c in geometry.columns))
        return hashlib.sha256(text.encode("utf-8")).hexdigest()
