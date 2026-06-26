"""Concrete measurement extraction helpers for cross-section geometry."""

from __future__ import annotations

from metrology_process_planner.domains.session.display_units import (
    format_length,
    resolved_display_unit,
)
from metrology_process_planner.rendering.cross_section.measurement_models import (
    MeasurementAnnotation,
)
from metrology_process_planner.rendering.cross_section.scene_models import (
    CompressionMetadata,
    MaterialShape,
)


def layer_thicknesses(
    shapes: tuple[MaterialShape, ...],
    units: str,
    display_units: str,
) -> tuple[MeasurementAnnotation, ...]:
    """Return layer-thickness annotations for visible material regions."""

    annotations: list[MeasurementAnnotation] = []
    seen: set[tuple[str, float]] = set()
    for shape in shapes:
        thickness = abs(shape.physical_bounds[3] - shape.physical_bounds[1])
        key = (shape.material_id, round(thickness, 9))
        if not shape.visible or thickness <= 0 or key in seen:
            continue
        seen.add(key)
        annotations.append(
            shape_measurement(
                shape, "layer_thickness", f"{shape.material_name} thickness",
                thickness, units, display_units, vertical=True,
            )
    )
    return tuple(annotations)

def feature_widths(
    shapes: tuple[MaterialShape, ...],
    units: str,
    display_units: str,
) -> tuple[MeasurementAnnotation, ...]:
    """Return feature-width annotations for visible material regions."""

    annotations: list[MeasurementAnnotation] = []
    seen: set[tuple[str, float]] = set()
    for shape in shapes:
        width = abs(shape.physical_bounds[2] - shape.physical_bounds[0])
        key = (shape.material_id, round(width, 9))
        if not shape.visible or width <= 0 or key in seen:
            continue
        seen.add(key)
        annotations.append(
            shape_measurement(
                shape, "feature_width", f"{shape.material_name} width",
                width, units, display_units, vertical=False,
            )
    )
    return tuple(annotations)

def surface_delta_measurements(
    surface_profiles: tuple[tuple[tuple[float, float], ...], ...],
    units: str,
    display_units: str,
) -> tuple[MeasurementAnnotation, ...]:
    """Return step-height, profile-delta, and trench-depth measurements."""

    points = tuple(point for profile in surface_profiles for point in profile)
    if len(points) < 2:
        return ()
    low = min(points, key=lambda point: point[1])
    high = max(points, key=lambda point: point[1])
    delta = abs(high[1] - low[1])
    if delta <= 0:
        return ()
    return _surface_delta_annotations(delta, (high[0], low[1]), (high[0], high[1]),
                                      units, display_units)

def compressed_extents(
    compression_metadata: CompressionMetadata,
    units: str,
    display_units: str,
) -> tuple[MeasurementAnnotation, ...]:
    """Return vertical extents for compressed physical regions."""

    if not compression_metadata.enabled:
        return ()
    annotations: list[MeasurementAnnotation] = []
    for index, z_range in enumerate(compression_metadata.physical_z_ranges):
        if len(z_range) != 2:
            continue
        low, high = z_range
        value = abs(high - low)
        if value <= 0:
            continue
        x = -0.08 - index * 0.04
        formatted = _format(value, units, display_units)
        annotations.append(
            MeasurementAnnotation(
                f"measurement-compressed-extent-{index + 1}",
                "compressed_vertical_extent",
                "Compressed vertical extent",
                value,
                _display_unit(value, units, display_units),
                formatted,
                ((x, low), (x, high)),
                ((x, low), (x, high)),
                (x, (low + high) / 2.0),
                caption=f"Compressed vertical extent: {formatted}",
            )
    )
    return tuple(annotations)

def representative_measurement_value(
    shapes: tuple[MaterialShape, ...],
    surface_profiles: tuple[tuple[tuple[float, float], ...], ...],
) -> float | None:
    """Return a representative positive measurement for auto unit selection."""

    values = [
        abs(shape.physical_bounds[3] - shape.physical_bounds[1])
        for shape in shapes
        if shape.visible and abs(shape.physical_bounds[3] - shape.physical_bounds[1]) > 0
    ]
    values.extend(_surface_delta_value(surface_profiles))
    return min(values) if values else None

def shape_measurement(
    shape: MaterialShape,
    kind: str,
    label: str,
    value: float,
    units: str,
    display_units: str,
    *,
    vertical: bool,
) -> MeasurementAnnotation:
    """Return one shape-derived measurement annotation."""

    physical_span = _shape_span(shape.physical_bounds, vertical)
    visual_span = _shape_span(shape.visual_bounds, vertical)
    formatted = _format(value, units, display_units)
    safe_label = label.lower().replace(" ", "-")
    return MeasurementAnnotation(
        f"measurement-{kind}-{shape.shape_id}-{safe_label}",
        kind,
        label,
        value,
        _display_unit(value, units, display_units),
        formatted,
        physical_span,
        visual_span,
        _midpoint(visual_span),
        (shape.shape_id,),
        f"{label}: {formatted}",
    )

def _surface_delta_annotations(
    delta: float,
    start: tuple[float, float],
    end: tuple[float, float],
    units: str,
    display_units: str,
) -> tuple[MeasurementAnnotation, ...]:
    formatted = _format(delta, units, display_units)
    unit = _display_unit(delta, units, display_units)
    span = (start, end)
    anchor = (end[0], (start[1] + end[1]) / 2.0)
    return (
        MeasurementAnnotation(
            "measurement-step-height", "step_height", "Step height", delta, unit,
            formatted, span, span, anchor, caption=f"Step height: {formatted}"
        ),
        MeasurementAnnotation(
            "measurement-profile-delta", "profile_delta", "Profile delta", delta, unit,
            formatted, span, span, anchor, caption=f"Profile delta: {formatted}"
        ),
        MeasurementAnnotation(
            "measurement-trench-depth", "trench_depth", "Trench depth", delta, unit,
            formatted, span, span, anchor, caption=f"Trench depth: {formatted}"
        ),
    )

def _shape_span(
    bounds: tuple[float, float, float, float],
    vertical: bool,
) -> tuple[tuple[float, float], tuple[float, float]]:
    left, bottom, right, top = bounds
    if vertical:
        x = right + max((right - left) * 0.08, 0.04)
        return ((x, bottom), (x, top))
    y = top + max((top - bottom) * 0.08, 0.04)
    return ((left, y), (right, y))


def _format(value: float, units: str, display_units: str) -> str:
    return format_length(value, units, display_units, precision=4)


def _display_unit(value: float, units: str, display_units: str) -> str:
    return resolved_display_unit(value, units, display_units)


def _surface_delta_value(
    surface_profiles: tuple[tuple[tuple[float, float], ...], ...],
) -> tuple[float, ...]:
    points = tuple(point for profile in surface_profiles for point in profile)
    if len(points) < 2:
        return ()
    delta = max(point[1] for point in points) - min(point[1] for point in points)
    return (abs(delta),) if delta else ()


def _midpoint(span: tuple[tuple[float, float], tuple[float, float]]) -> tuple[float, float]:
    return ((span[0][0] + span[1][0]) / 2.0, (span[0][1] + span[1][1]) / 2.0)
