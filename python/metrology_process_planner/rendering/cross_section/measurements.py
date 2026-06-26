"""Measurement annotation API for cross-section scenes."""

from __future__ import annotations

from metrology_process_planner.domains.session.display_units import resolved_display_unit
from metrology_process_planner.rendering.cross_section.measurement_extractors import (
    compressed_extents,
    feature_widths,
    layer_thicknesses,
    representative_measurement_value,
    surface_delta_measurements,
)
from metrology_process_planner.rendering.cross_section.measurement_models import (
    MeasurementAnnotation,
)
from metrology_process_planner.rendering.cross_section.scene_models import (
    CompressionMetadata,
    MaterialShape,
)

MEASUREMENT_UNAVAILABLE_WARNING = "RENDER_MEASUREMENT_UNAVAILABLE"


def build_measurement_annotations(
    shapes: tuple[MaterialShape, ...],
    surface_profiles: tuple[tuple[tuple[float, float], ...], ...],
    compression_metadata: CompressionMetadata,
    units: str,
    display_unit_preference: str = "auto",
) -> tuple[MeasurementAnnotation, ...]:
    """Extract supported measurements from physical and projected geometry."""

    display_units = resolved_display_unit(
        representative_measurement_value(shapes, surface_profiles),
        units,
        display_unit_preference,
    )
    annotations: list[MeasurementAnnotation] = []
    annotations.extend(layer_thicknesses(shapes, units, display_units))
    annotations.extend(feature_widths(shapes, units, display_units))
    annotations.extend(surface_delta_measurements(surface_profiles, units, display_units))
    annotations.extend(compressed_extents(compression_metadata, units, display_units))
    return tuple(annotations)


def measurement_warnings(
    annotations: tuple[MeasurementAnnotation, ...],
) -> tuple[str, ...]:
    """Return non-fatal warnings when scene geometry cannot support measurements."""

    return () if annotations else (MEASUREMENT_UNAVAILABLE_WARNING,)


def measurement_report_summary(
    annotations: tuple[MeasurementAnnotation, ...],
) -> dict[str, object]:
    """Return compact measurement data for report captions and summaries."""

    return {
        "measurement_count": len(annotations),
        "measurements": tuple(annotation.to_dict() for annotation in annotations),
        "caption": measurement_caption(annotations),
    }


def measurement_caption(annotations: tuple[MeasurementAnnotation, ...]) -> str:
    """Return a compact, renderer-neutral measurement caption."""

    if not annotations:
        return "No cross-section measurements were available from solver geometry."
    captions = [item.caption or f"{item.label}: {item.formatted_value}" for item in annotations[:4]]
    extra = len(annotations) - len(captions)
    suffix = f"; +{extra} more" if extra > 0 else ""
    return "; ".join(captions) + suffix
