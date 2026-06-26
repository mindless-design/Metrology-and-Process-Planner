"""Shape-derived measurement annotations for cross-section scenes."""

from __future__ import annotations

from metrology_process_planner.domains.session.display_units import format_length
from metrology_process_planner.rendering.cross_section.measurement_models import (
    MeasurementAnnotation,
)
from metrology_process_planner.rendering.cross_section.scene_models import MaterialShape


def layer_thicknesses(
    shapes: tuple[MaterialShape, ...],
    units: str,
    display_units: str,
) -> tuple[MeasurementAnnotation, ...]:
    """Return unique visible layer-thickness annotations."""

    annotations: list[MeasurementAnnotation] = []
    seen: set[tuple[str, float]] = set()
    for shape in shapes:
        thickness = _visible_thickness(shape)
        key = (shape.material_id, round(thickness, 9))
        if thickness <= 0 or key in seen:
            continue
        seen.add(key)
        annotations.append(
            _shape_measurement(
                shape,
                "layer_thickness",
                f"{shape.material_name} thickness",
                thickness,
                units,
                display_units,
                vertical=True,
            )
        )
    return tuple(annotations)


def feature_widths(
    shapes: tuple[MaterialShape, ...],
    units: str,
    display_units: str,
) -> tuple[MeasurementAnnotation, ...]:
    """Return unique visible feature-width annotations."""

    annotations: list[MeasurementAnnotation] = []
    seen: set[tuple[str, float]] = set()
    for shape in shapes:
        if not shape.visible:
            continue
        width = abs(shape.physical_bounds[2] - shape.physical_bounds[0])
        key = (shape.material_id, round(width, 9))
        if width <= 0 or key in seen:
            continue
        seen.add(key)
        annotations.append(
            _shape_measurement(
                shape,
                "feature_width",
                f"{shape.material_name} width",
                width,
                units,
                display_units,
                vertical=False,
            )
        )
    return tuple(annotations)


def _shape_measurement(
    shape: MaterialShape,
    kind: str,
    label: str,
    value: float,
    units: str,
    display_units: str,
    *,
    vertical: bool,
) -> MeasurementAnnotation:
    physical_span = _shape_span(shape.physical_bounds, vertical)
    visual_span = _shape_span(shape.visual_bounds, vertical)
    formatted = format_length(value, units, display_units, precision=4)
    safe_label = label.lower().replace(" ", "-")
    return MeasurementAnnotation(
        f"measurement-{kind}-{shape.shape_id}-{safe_label}",
        kind,
        label,
        value,
        display_units,
        formatted,
        physical_span,
        visual_span,
        _midpoint(visual_span),
        (shape.shape_id,),
        f"{label}: {formatted}",
    )


def _visible_thickness(shape: MaterialShape) -> float:
    if not shape.visible:
        return 0.0
    return abs(shape.physical_bounds[3] - shape.physical_bounds[1])


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


def _midpoint(span: tuple[tuple[float, float], tuple[float, float]]) -> tuple[float, float]:
    return ((span[0][0] + span[1][0]) / 2.0, (span[0][1] + span[1][1]) / 2.0)
