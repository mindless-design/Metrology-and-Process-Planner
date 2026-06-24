"""Profiles and options for the hybrid cross-section solver."""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Optional


class ProcessProfile(str, Enum):
    """Process operation profile families."""

    SUBSTRATE = "substrate"
    BLANKET_DEPOSITION = "blanket_deposition"
    PATTERNED_DEPOSITION = "patterned_deposition"
    CONFORMAL_DEPOSITION = "conformal_deposition"
    DIRECTIONAL_ETCH = "directional_etch"
    ISOTROPIC_ETCH = "isotropic_etch"
    TAPERED_ETCH = "tapered_etch"
    PLANARIZATION = "planarization"
    CMP_PLANARIZATION = "cmp_planarization"
    ANNOTATION_ONLY = "annotation_only"


@dataclass(frozen=True)
class ConformalProfile:
    """Coverage factors for exposed-surface conformal deposition."""

    top_coverage: float = 1.0
    sidewall_coverage: float = 1.0
    bottom_coverage: float = 1.0


@dataclass(frozen=True)
class EtchProfile:
    """Etch geometry and material behavior controls."""

    depth: float
    targets: tuple[str, ...] = ()
    stop_materials: tuple[str, ...] = ()
    overetch_factor: float = 1.0
    lateral_attack: float = 0.0
    sidewall_angle_deg: Optional[float] = None
    top_cd_bias: float = 0.0
    bottom_cd_bias: float = 0.0


@dataclass(frozen=True)
class PlanarizationProfile:
    """Ideal or CMP heuristic planarization controls."""

    target_height: Optional[float] = None
    stop_materials: tuple[str, ...] = ()
    overpolish: float = 0.0
    density_window: float = 1.0
    dishing_coefficient: float = 0.0
    erosion_coefficient: float = 0.0


@dataclass(frozen=True)
class ApproximationPolicy:
    """Numerical approximation controls and thresholds."""

    grid_resolution: float = 0.05
    min_feature_width: float = 0.05
    allow_heuristics: bool = True
    emit_resolution_diagnostics: bool = True


@dataclass(frozen=True)
class SolverOptions:
    """Runtime options for solver execution."""

    x_min: float = 0.0
    x_max: float = 10.0
    sample_count: int = 201
    frame_every_step: bool = True
    point_sample_xs: tuple[float, ...] = ()
    cutline_x_min: Optional[float] = None
    cutline_x_max: Optional[float] = None
    approximation_policy: ApproximationPolicy = ApproximationPolicy()
