"""Private sampled-geometry helper functions."""

from __future__ import annotations

from dataclasses import replace
from typing import Callable

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
    MaterialRegion,
    StackColumn,
    StackGeometry2D,
)
from metrology_process_planner.solver.solver_profiles import ConformalProfile, EtchProfile


def _make_samples(x_min: float, x_max: float, count: int) -> tuple[float, ...]:
    if count <= 1:
        return (x_min,)
    step = (x_max - x_min) / (count - 1)
    return tuple(round(x_min + index * step, 9) for index in range(count))


def _make_column(x: float, *intervals: MaterialInterval) -> StackColumn:
    return StackColumn(x, tuple(intervals))


def _map_columns(
    geometry: StackGeometry2D,
    fn: Callable[[StackColumn], StackColumn],
) -> StackGeometry2D:
    return _replace_columns(geometry, tuple(fn(column) for column in geometry.columns))


def _replace_columns(
    geometry: StackGeometry2D,
    columns: tuple[StackColumn, ...],
    *,
    conformal_layers: tuple[ConformalLayerMetadata, ...] = (),
    pinch_off_regions: tuple[PinchOffRegion, ...] = (),
    undercut_regions: tuple[UndercutRegion, ...] = (),
    tapered_regions: tuple[TaperedRegion, ...] = (),
) -> StackGeometry2D:
    return StackGeometry2D(
        columns,
        geometry.regions,
        geometry.void_regions,
        geometry.seam_regions,
        geometry.pinch_off_regions + pinch_off_regions,
        geometry.undercut_regions + undercut_regions,
        geometry.tapered_regions + tapered_regions,
        geometry.conformal_layers + conformal_layers,
    )


def _add_top(column: StackColumn, material_id: str, thickness: float) -> StackColumn:
    interval = MaterialInterval(material_id, column.top, column.top + thickness)
    return replace(column, intervals=column.intervals + (interval,))


def _is_masked(x: float, mask: tuple[MaskInterval, ...], polarity: MaskPolarity) -> bool:
    inside = any(interval.contains(x) for interval in mask) if mask else True
    return not inside if polarity is MaskPolarity.INVERTED else inside


def _grow_conformal_column(
    grown: list[list[MaterialInterval]],
    geometry: StackGeometry2D,
    index: int,
    material_id: str,
    thickness: float,
    profile: ConformalProfile,
) -> None:
    column = geometry.columns[index]
    top = thickness * profile.top_coverage
    grown[index].append(MaterialInterval(material_id, column.top, column.top + top))
    sidewall = _sidewall_growth(geometry, index, thickness, profile)
    if sidewall > 0:
        grown[index].append(MaterialInterval(material_id, 0.0, min(column.top, sidewall)))


def _sidewall_growth(
    geometry: StackGeometry2D,
    index: int,
    thickness: float,
    profile: ConformalProfile,
) -> float:
    column = geometry.columns[index]
    left = geometry.columns[index - 1].top if index else column.top
    right = geometry.columns[index + 1].top if index + 1 < len(geometry.columns) else column.top
    step_height = max(0.0, left - column.top, right - column.top)
    bottom = thickness * profile.bottom_coverage if step_height > 0 else 0.0
    return min(step_height, thickness * profile.sidewall_coverage + bottom)


def _clean(intervals: tuple[MaterialInterval, ...]) -> tuple[MaterialInterval, ...]:
    return tuple(item for item in intervals if item.z_max > item.z_min)


def _etch_column(column: StackColumn, profile: EtchProfile, depth: float) -> StackColumn:
    remaining = depth
    intervals = list(column.intervals)
    while remaining > 0 and intervals:
        top = intervals[-1]
        if top.material_id in profile.stop_materials:
            break
        if profile.targets and top.material_id not in profile.targets:
            break
        remove = min(remaining, top.z_max - top.z_min)
        remaining -= remove
        intervals = _remove_top(intervals, top, remove)
    return replace(column, intervals=tuple(intervals))


def _remove_top(
    intervals: list[MaterialInterval],
    top: MaterialInterval,
    remove: float,
) -> list[MaterialInterval]:
    if remove >= top.z_max - top.z_min:
        intervals.pop()
    else:
        intervals[-1] = replace(top, z_max=top.z_max - remove)
    return intervals


def _laterally_attacked_xs(geometry: StackGeometry2D, radius: float) -> set[float]:
    exposed = {column.x for column in geometry.columns if column.intervals}
    return {
        column.x
        for column in geometry.columns
        if any(abs(column.x - x) <= radius for x in exposed)
    }


def _median_top(geometry: StackGeometry2D) -> float:
    tops = sorted(column.top for column in geometry.columns)
    return tops[len(tops) // 2] if tops else 0.0


def _clip_column(column: StackColumn, target: float) -> StackColumn:
    clipped = []
    for interval in column.intervals:
        if interval.z_min < target:
            clipped.append(replace(interval, z_max=min(interval.z_max, target)))
    return replace(column, intervals=_clean(tuple(clipped)))


def _material_density(geometry: StackGeometry2D, materials: tuple[str, ...]) -> float:
    if not geometry.columns or not materials:
        return 0.5
    hits = sum(_top_is_material(column, materials) for column in geometry.columns)
    return hits / len(geometry.columns)


def _top_is_material(column: StackColumn, materials: tuple[str, ...]) -> bool:
    return bool(column.intervals and column.intervals[-1].material_id in materials)


def _regions(geometry: StackGeometry2D) -> tuple[MaterialRegion, ...]:
    dx = _sample_width(geometry)
    return tuple(
        _region(column, interval, dx)
        for column in geometry.columns
        for interval in column.intervals
    )


def _region(column: StackColumn, interval: MaterialInterval, dx: float) -> MaterialRegion:
    return MaterialRegion(
        interval.material_id,
        column.x - dx / 2,
        column.x + dx / 2,
        interval.z_min,
        interval.z_max,
    )


def _sample_width(geometry: StackGeometry2D) -> float:
    if len(geometry.columns) < 2:
        return 1.0
    return abs(geometry.columns[1].x - geometry.columns[0].x)


def _material_order(geometry: StackGeometry2D) -> tuple[str, ...]:
    return tuple(
        dict.fromkeys(
            interval.material_id
            for column in geometry.columns
            for interval in column.intervals
        )
    )
