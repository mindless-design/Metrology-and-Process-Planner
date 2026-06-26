"""Operation bodies for the sampled geometry kernel."""

from __future__ import annotations

from metrology_process_planner.domains.process.steps import MaskPolarity
from metrology_process_planner.solver.geometry_models import (
    MaskInterval,
    MaterialInterval,
    RenderProjection,
    StackColumn,
    StackGeometry2D,
)
from metrology_process_planner.solver.sampled_advanced_helpers import (
    conformal_metadata,
    etch_profile_masked,
    pinch_off_regions,
    tapered_regions,
    undercut_region,
)
from metrology_process_planner.solver.sampled_geometry_helpers import (
    _add_top,
    _clean,
    _clip_column,
    _etch_column,
    _grow_conformal_column,
    _is_masked,
    _laterally_attacked_xs,
    _make_column,
    _map_columns,
    _material_density,
    _material_order,
    _median_top,
    _regions,
    _replace_columns,
)
from metrology_process_planner.solver.solver_profiles import (
    ConformalProfile,
    EtchProfile,
    PlanarizationProfile,
)


def deposit_blanket(
    geometry: StackGeometry2D,
    material_id: str,
    thickness: float,
) -> StackGeometry2D:
    """Deposit a topography-following film on every sampled column."""

    return _map_columns(geometry, lambda column: _add_top(column, material_id, thickness))


def deposit_patterned(
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
    geometry: StackGeometry2D,
    material_id: str,
    thickness: float,
    profile: ConformalProfile,
    source_step_id: str,
    mask: tuple[MaskInterval, ...],
) -> StackGeometry2D:
    """Approximate exposed-surface growth with top and sidewall coverage."""

    grown = [list(column.intervals) for column in geometry.columns]
    for index, _ in enumerate(geometry.columns):
        _grow_conformal_column(grown, geometry, index, material_id, thickness, profile)
    columns = tuple(
        _make_column(column.x, *_clean(tuple(grown[index])))
        for index, column in enumerate(geometry.columns)
    )
    return _replace_columns(
        geometry,
        columns,
        conformal_layers=(conformal_metadata(material_id, source_step_id, thickness, profile),),
        pinch_off_regions=pinch_off_regions(geometry, mask, source_step_id, thickness, profile),
    )


def etch_directional(geometry: StackGeometry2D, profile: EtchProfile) -> StackGeometry2D:
    """Remove target materials top-down until depth or blocker is reached."""

    depth = profile.depth * profile.overetch_factor
    return _map_columns(
        geometry,
        lambda column: _etch_column(column, profile, depth)
        if etch_profile_masked(column.x, profile)
        else column,
    )


def etch_isotropic(geometry: StackGeometry2D, profile: EtchProfile) -> StackGeometry2D:
    """Approximate isotropic exposed-boundary etch with lateral attack."""

    attacked = _laterally_attacked_xs(geometry, profile.lateral_attack or profile.depth)
    etched = _map_columns(
        geometry,
        lambda column: _etch_column(column, profile, profile.depth)
        if column.x in attacked and etch_profile_masked(column.x, profile)
        else column,
    )
    return _replace_columns(
        etched,
        etched.columns,
        undercut_regions=undercut_region(geometry, attacked, profile, profile.step_id),
    )


def etch_tapered(geometry: StackGeometry2D, profile: EtchProfile) -> StackGeometry2D:
    """Approximate tapered etch using the target etch depth."""

    depth = profile.depth * profile.overetch_factor
    etched = _map_columns(
        geometry,
        lambda column: _etch_column(column, profile, depth)
        if etch_profile_masked(column.x, profile)
        else column,
    )
    return _replace_columns(
        etched,
        etched.columns,
        tapered_regions=tapered_regions(geometry, profile, profile.step_id),
    )


def planarize(geometry: StackGeometry2D, profile: PlanarizationProfile) -> StackGeometry2D:
    """Clip all stacks to an ideal planar target height."""

    target = profile.target_height if profile.target_height is not None else _median_top(geometry)
    return _map_columns(geometry, lambda column: _clip_column(column, target))


def cmp_planarize(geometry: StackGeometry2D, profile: PlanarizationProfile) -> StackGeometry2D:
    """Apply explicit heuristic CMP overpolish, dishing, and erosion."""

    base = profile.target_height if profile.target_height is not None else _median_top(geometry)
    density = _material_density(geometry, profile.stop_materials)
    target = base - profile.overpolish - profile.dishing_coefficient * density
    target -= profile.erosion_coefficient * (1.0 - density)
    return _map_columns(geometry, lambda column: _clip_column(column, target))


def make_render_projection(geometry: StackGeometry2D) -> RenderProjection:
    """Build render-ready material regions and surface points."""

    return RenderProjection(
        _regions(geometry),
        geometry.surface,
        _material_order(geometry),
        void_regions=geometry.void_regions,
        seam_regions=geometry.seam_regions,
        pinch_off_regions=geometry.pinch_off_regions,
        undercut_regions=geometry.undercut_regions,
        tapered_regions=geometry.tapered_regions,
        conformal_layers=geometry.conformal_layers,
    )


def substrate_columns(
    xs: tuple[float, ...],
    material_id: str,
    thickness: float,
) -> tuple[StackColumn, ...]:
    """Return substrate columns for sampled x positions."""

    return tuple(_make_column(x, MaterialInterval(material_id, 0.0, thickness)) for x in xs)
