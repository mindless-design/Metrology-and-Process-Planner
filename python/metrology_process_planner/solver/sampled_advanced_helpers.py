"""Advanced metadata helpers for the sampled geometry backend."""

from __future__ import annotations

from math import radians, tan

from metrology_process_planner.domains.process.steps import MaskPolarity
from metrology_process_planner.solver.advanced_geometry_models import (
    ConformalLayerMetadata,
    PinchOffRegion,
    TaperedRegion,
    UndercutRegion,
)
from metrology_process_planner.solver.geometry_models import (
    MaskInterval,
    MaterialInterval,
    StackColumn,
    StackGeometry2D,
)
from metrology_process_planner.solver.solver_profiles import ConformalProfile, EtchProfile


def conformal_metadata(
    material_id: str,
    step_id: str,
    thickness: float,
    profile: ConformalProfile,
) -> ConformalLayerMetadata:
    """Return conformal-layer metadata for render projection."""

    return ConformalLayerMetadata(
        material_id,
        step_id,
        thickness,
        profile.top_coverage,
        profile.sidewall_coverage,
        profile.bottom_coverage,
        thin_layer_flag=thickness <= 10.0,
    )


def pinch_off_regions(
    geometry: StackGeometry2D,
    mask: tuple[MaskInterval, ...],
    step_id: str,
    thickness: float,
    profile: ConformalProfile,
) -> tuple[PinchOffRegion, ...]:
    """Return narrow feature closure markers from conformal sidewall growth."""

    growth = 2 * thickness * profile.sidewall_coverage
    regions: list[PinchOffRegion] = []
    for interval in mask:
        if interval.width <= growth:
            regions.append(_pinch_off_region(geometry, interval, step_id, thickness, growth))
    return tuple(regions)


def undercut_region(
    geometry: StackGeometry2D,
    attacked: set[float],
    profile: EtchProfile,
    step_id: str,
) -> tuple[UndercutRegion, ...]:
    """Return undercut metadata for attacked target intervals."""

    xs = sorted(attacked)
    target_intervals = _target_intervals(geometry, attacked, profile)
    if not xs or not target_intervals:
        return ()
    return (
        UndercutRegion(
            min(xs),
            max(xs),
            min(interval.z_min for interval in target_intervals),
            max(interval.z_max for interval in target_intervals),
            step_id,
            profile.lateral_attack or profile.depth,
            profile.targets,
        ),
    )


def tapered_regions(
    geometry: StackGeometry2D,
    profile: EtchProfile,
    step_id: str,
) -> tuple[TaperedRegion, ...]:
    """Return tapered-opening metadata from active target columns."""

    if profile.sidewall_angle_deg is None:
        return ()
    targets = _active_target_columns(geometry, profile)
    if not targets:
        return ()
    top_width = max(column.x for column in targets) - min(column.x for column in targets)
    if top_width <= 0:
        return ()
    return (_tapered_region(targets, profile, step_id, top_width),)


def etch_profile_masked(x: float, profile: EtchProfile) -> bool:
    """Return whether x is active under an etch profile mask."""

    inside = any(interval.contains(x) for interval in profile.mask) if profile.mask else True
    return not inside if profile.mask_polarity == MaskPolarity.INVERTED.value else inside


def _pinch_off_region(
    geometry: StackGeometry2D,
    interval: MaskInterval,
    step_id: str,
    thickness: float,
    growth: float,
) -> PinchOffRegion:
    columns = tuple(
        column for column in geometry.columns if interval.x_min <= column.x <= interval.x_max
    )
    top = min((column.top for column in columns), default=0.0)
    side_height = max((column.top for column in geometry.columns), default=top) - top
    return PinchOffRegion(
        interval.x_min,
        interval.x_max,
        top,
        top + max(thickness, side_height),
        step_id,
        interval.width,
        growth,
    )


def _target_intervals(
    geometry: StackGeometry2D,
    attacked: set[float],
    profile: EtchProfile,
) -> tuple[MaterialInterval, ...]:
    return tuple(
        interval
        for column in geometry.columns
        if column.x in attacked
        for interval in column.intervals
        if not profile.targets or interval.material_id in profile.targets
    )


def _active_target_columns(
    geometry: StackGeometry2D,
    profile: EtchProfile,
) -> tuple[StackColumn, ...]:
    return tuple(
        column
        for column in geometry.columns
        if etch_profile_masked(column.x, profile)
        and column.intervals
        and (not profile.targets or column.intervals[-1].material_id in profile.targets)
    )


def _tapered_region(
    targets: tuple[StackColumn, ...],
    profile: EtchProfile,
    step_id: str,
    top_width: float,
) -> TaperedRegion:
    z_top = max(column.top for column in targets)
    z_bottom = max(0.0, z_top - profile.depth * profile.overetch_factor)
    bottom_width = _bottom_width(profile, top_width, z_top - z_bottom)
    center = (min(column.x for column in targets) + max(column.x for column in targets)) / 2.0
    return TaperedRegion(
        center - (top_width + profile.top_cd_bias) / 2.0,
        center + (top_width + profile.top_cd_bias) / 2.0,
        center - bottom_width / 2.0,
        center + bottom_width / 2.0,
        z_top,
        z_bottom,
        step_id,
        profile.sidewall_angle_deg,
        profile.targets,
        profile.stop_materials,
    )


def _bottom_width(profile: EtchProfile, top_width: float, depth: float) -> float:
    recession = depth * tan(radians(max(0.0, 90.0 - float(profile.sidewall_angle_deg or 90.0))))
    return max(0.0, top_width - 2 * recession + profile.bottom_cd_bias)
