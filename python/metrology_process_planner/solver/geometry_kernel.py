"""Geometry kernel interface for process solver backends."""

from __future__ import annotations

from typing import Protocol

from metrology_process_planner.domains.process.steps import MaskPolarity
from metrology_process_planner.solver.geometry_models import (
    CutlineSample,
    MaskInterval,
    PointSample,
    RenderProjection,
    StackGeometry2D,
)
from metrology_process_planner.solver.solver_profiles import (
    ConformalProfile,
    EtchProfile,
    PlanarizationProfile,
)


class GeometryKernel(Protocol):
    """Geometry backend contract for operation executors."""

    def initialize_substrate(self, material_id: str, thickness: float) -> StackGeometry2D:
        """Create the initial substrate geometry."""

    def deposit_blanket(
        self,
        geometry: StackGeometry2D,
        material_id: str,
        thickness: float,
    ) -> StackGeometry2D:
        """Deposit a topography-following blanket film."""

    def deposit_patterned(
        self,
        geometry: StackGeometry2D,
        material_id: str,
        thickness: float,
        mask: tuple[MaskInterval, ...],
        polarity: MaskPolarity,
    ) -> StackGeometry2D:
        """Deposit material inside a direct or inverted mask."""

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

    def etch_directional(
        self,
        geometry: StackGeometry2D,
        profile: EtchProfile,
    ) -> StackGeometry2D:
        """Remove target materials from the top down."""

    def etch_isotropic(self, geometry: StackGeometry2D, profile: EtchProfile) -> StackGeometry2D:
        """Remove target materials with lateral attack approximation."""

    def etch_tapered(self, geometry: StackGeometry2D, profile: EtchProfile) -> StackGeometry2D:
        """Remove target materials using a tapered-profile approximation."""

    def planarize(
        self,
        geometry: StackGeometry2D,
        profile: PlanarizationProfile,
    ) -> StackGeometry2D:
        """Apply ideal planarization."""

    def cmp_planarize(
        self,
        geometry: StackGeometry2D,
        profile: PlanarizationProfile,
    ) -> StackGeometry2D:
        """Apply heuristic CMP planarization."""

    def extract_point_stack(self, geometry: StackGeometry2D, x: float) -> PointSample:
        """Extract one stack at the nearest x position."""

    def extract_cutline_profile(
        self,
        geometry: StackGeometry2D,
        x_min: float,
        x_max: float,
    ) -> tuple[CutlineSample, ...]:
        """Extract all sampled stacks along a cutline."""

    def make_render_projection(self, geometry: StackGeometry2D) -> RenderProjection:
        """Create render-ready regions and surface data."""

    def compute_signature(self, geometry: StackGeometry2D) -> str:
        """Compute a deterministic geometry signature."""
