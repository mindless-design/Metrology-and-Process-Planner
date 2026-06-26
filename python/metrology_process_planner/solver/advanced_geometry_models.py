"""Advanced geometry metadata models for solver and renderer contracts."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class VoidRegion:
    """Explicit void or enclosed gap detected by geometry operations."""

    x_min: float
    x_max: float
    z_min: float
    z_max: float
    source_step_id: str = ""
    reason: str = ""


@dataclass(frozen=True)
class SeamRegion:
    """Likely seam location from closing conformal fronts."""

    x: float
    z_min: float
    z_max: float
    source_step_id: str = ""
    reason: str = ""


@dataclass(frozen=True)
class PinchOffRegion:
    """Narrow feature closure predicted by the geometry approximation."""

    x_min: float
    x_max: float
    z_min: float
    z_max: float
    source_step_id: str = ""
    gap_width: float = 0.0
    closing_thickness: float = 0.0


@dataclass(frozen=True)
class UndercutRegion:
    """Lateral material removal created by isotropic etching."""

    x_min: float
    x_max: float
    z_min: float
    z_max: float
    source_step_id: str = ""
    etch_distance: float = 0.0
    target_materials: tuple[str, ...] = ()


@dataclass(frozen=True)
class TaperedRegion:
    """Renderable tapered etch opening with sloped-sidewall metadata."""

    x_top_min: float
    x_top_max: float
    x_bottom_min: float
    x_bottom_max: float
    z_top: float
    z_bottom: float
    source_step_id: str = ""
    sidewall_angle_deg: float | None = None
    target_materials: tuple[str, ...] = ()
    stop_materials: tuple[str, ...] = ()

    @property
    def polygon(self) -> tuple[tuple[float, float], ...]:
        """Return a closed renderable polygon for the tapered opening."""

        return (
            (self.x_top_min, self.z_top),
            (self.x_top_max, self.z_top),
            (self.x_bottom_max, self.z_bottom),
            (self.x_bottom_min, self.z_bottom),
        )


@dataclass(frozen=True)
class ConformalLayerMetadata:
    """Metadata for material grown by conformal exposed-surface deposition."""

    material_id: str
    source_step_id: str
    physical_thickness: float
    top_coverage_factor: float
    sidewall_coverage_factor: float
    bottom_coverage_factor: float
    thin_layer_flag: bool = False
    approximation: str = "sampled_exposed_surface_growth"
