"""Geometry helpers for cross-section visual projection."""

from __future__ import annotations

from metrology_process_planner.domains.process import StackColumn, StackGeometry2D
from metrology_process_planner.rendering.cross_section.scene_models import MaterialShape


def material_shape(
    column_index: int,
    interval_index: int,
    material_id: str,
    material_name: str,
    color: str,
    physical: tuple[float, float, float, float],
    visual: tuple[float, float, float, float],
    physical_thickness: float,
    compressed: bool,
    exaggerated: bool,
) -> MaterialShape:
    """Build one material shape from physical and visual bounds."""

    shape_id = f"shape-{column_index:03d}-{interval_index:03d}-{material_id}"
    return MaterialShape(
        shape_id,
        material_id,
        material_name,
        "",
        physical,
        visual,
        physical,
        visual,
        True,
        {"fill": color, "stroke": "#333333"},
        (),
        thin_layer_flag=physical_thickness <= 10.0,
        compressed_flag=compressed,
        exaggerated_flag=exaggerated,
    )


def column_edges(geometry: StackGeometry2D) -> tuple[tuple[float, float, StackColumn], ...]:
    """Return inferred left and right x bounds for sampled columns."""

    columns = tuple(sorted(geometry.columns, key=lambda item: item.x))
    if not columns:
        return ()
    if len(columns) == 1:
        return ((columns[0].x - 0.5, columns[0].x + 0.5, columns[0]),)
    mids = tuple(
        (columns[index].x + columns[index + 1].x) / 2.0
        for index in range(len(columns) - 1)
    )
    first = columns[0].x - (mids[0] - columns[0].x)
    last = columns[-1].x + (columns[-1].x - mids[-1])
    edges = (first,) + mids + (last,)
    return tuple((edges[index], edges[index + 1], column) for index, column in enumerate(columns))


def geometry_bounds(geometry: StackGeometry2D) -> tuple[float, float, float, float]:
    """Return physical bounds for sampled stack geometry."""

    edges = column_edges(geometry)
    if not edges:
        return (0.0, 0.0, 1.0, 1.0)
    z_values = [
        value
        for column in geometry.columns
        for interval in column.intervals
        for value in (interval.z_min, interval.z_max)
    ] or [0.0, 1.0]
    return (edges[0][0], min(z_values), edges[-1][1], max(z_values))


def override_notes(overrides: tuple[tuple[str, float, float], ...]) -> tuple[str, ...]:
    """Return human-readable notes for visual thickness overrides."""

    if not overrides:
        return ()
    materials = ", ".join(sorted({item[0] for item in overrides}))
    return (f"Thin-layer visual thickness override applied to: {materials}.",)
