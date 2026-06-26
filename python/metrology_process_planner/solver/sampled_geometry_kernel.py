"""Sampled-column geometry backend for the hybrid process solver."""

from __future__ import annotations

import hashlib

from metrology_process_planner.domains.process.steps import MaskPolarity
from metrology_process_planner.solver.geometry_models import (
    CutlineSample,
    MaskInterval,
    PointSample,
    RenderProjection,
    StackGeometry2D,
)
from metrology_process_planner.solver.sampled_geometry_helpers import _make_samples
from metrology_process_planner.solver.sampled_kernel_operations import (
    cmp_planarize,
    deposit_blanket,
    deposit_conformal,
    deposit_patterned,
    etch_directional,
    etch_isotropic,
    etch_tapered,
    make_render_projection,
    planarize,
    substrate_columns,
)
from metrology_process_planner.solver.solver_profiles import (
    ConformalProfile,
    EtchProfile,
    PlanarizationProfile,
)


class SampledGeometryKernel:
    """Useful v1 geometry backend based on sampled material stacks."""

    def __init__(self, x_min: float = 0.0, x_max: float = 10.0, sample_count: int = 201) -> None:
        self.xs = _make_samples(x_min, x_max, sample_count)

    def initialize_substrate(self, material_id: str, thickness: float) -> StackGeometry2D:
        """Create a flat substrate stack across the sampled x range."""

        return StackGeometry2D(substrate_columns(self.xs, material_id, thickness))

    def deposit_blanket(
        self,
        geometry: StackGeometry2D,
        material_id: str,
        thickness: float,
    ) -> StackGeometry2D:
        """Deposit a topography-following film on every sampled column."""

        return deposit_blanket(geometry, material_id, thickness)

    def deposit_patterned(
        self,
        geometry: StackGeometry2D,
        material_id: str,
        thickness: float,
        mask: tuple[MaskInterval, ...],
        polarity: MaskPolarity,
    ) -> StackGeometry2D:
        """Deposit a film in direct or inverted mask intervals."""

        return deposit_patterned(geometry, material_id, thickness, mask, polarity)

    def deposit_conformal(
        self,
        geometry: StackGeometry2D,
        material_id: str,
        thickness: float,
        profile: ConformalProfile,
        source_step_id: str = "",
        mask: tuple[MaskInterval, ...] = (),
    ) -> StackGeometry2D:
        """Grow material from exposed surfaces."""

        return deposit_conformal(geometry, material_id, thickness, profile, source_step_id, mask)

    def etch_directional(self, geometry: StackGeometry2D, profile: EtchProfile) -> StackGeometry2D:
        """Remove target materials from the top down."""

        return etch_directional(geometry, profile)

    def etch_isotropic(self, geometry: StackGeometry2D, profile: EtchProfile) -> StackGeometry2D:
        """Remove target materials with lateral attack approximation."""

        return etch_isotropic(geometry, profile)

    def etch_tapered(self, geometry: StackGeometry2D, profile: EtchProfile) -> StackGeometry2D:
        """Remove target materials using a tapered-profile approximation."""

        return etch_tapered(geometry, profile)

    def planarize(
        self,
        geometry: StackGeometry2D,
        profile: PlanarizationProfile,
    ) -> StackGeometry2D:
        """Apply ideal planarization."""

        return planarize(geometry, profile)

    def cmp_planarize(
        self,
        geometry: StackGeometry2D,
        profile: PlanarizationProfile,
    ) -> StackGeometry2D:
        """Apply heuristic CMP planarization."""

        return cmp_planarize(geometry, profile)

    def extract_point_stack(self, geometry: StackGeometry2D, x: float) -> PointSample:
        """Extract one stack at the nearest x position."""

        column = min(geometry.columns, key=lambda item: abs(item.x - x))
        return PointSample(column.x, column.intervals)

    def extract_cutline_profile(
        self,
        geometry: StackGeometry2D,
        x_min: float,
        x_max: float,
    ) -> tuple[CutlineSample, ...]:
        """Extract all sampled stacks along a cutline."""

        return tuple(
            CutlineSample(column.x, column.intervals)
            for column in geometry.columns
            if x_min <= column.x <= x_max
        )

    def make_render_projection(self, geometry: StackGeometry2D) -> RenderProjection:
        """Create render-ready regions and surface data."""

        return make_render_projection(geometry)

    def compute_signature(self, geometry: StackGeometry2D) -> str:
        """Compute a deterministic geometry signature."""

        text = repr(tuple((c.x, c.intervals) for c in geometry.columns))
        return hashlib.sha256(text.encode("utf-8")).hexdigest()
