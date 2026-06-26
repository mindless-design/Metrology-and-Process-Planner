"""Cross-section scene dataclass assembly helpers."""

from __future__ import annotations

import metrology_process_planner.rendering.cross_section.scene_parts as scene_parts
from metrology_process_planner.domains.process import ProcessFrame
from metrology_process_planner.domains.session.display_units import resolved_display_unit
from metrology_process_planner.rendering.cross_section.advanced_scene_metadata import (
    advanced_annotations,
    advanced_highlights,
)
from metrology_process_planner.rendering.cross_section.filtering import FilteredStackGeometry
from metrology_process_planner.rendering.cross_section.measurement_models import (
    MeasurementAnnotation,
)
from metrology_process_planner.rendering.cross_section.models import RenderIntent, RenderProfile
from metrology_process_planner.rendering.cross_section.projection import RenderProjectionPlan
from metrology_process_planner.rendering.cross_section.scene_metadata import (
    scene_title,
    source_refs,
)
from metrology_process_planner.rendering.cross_section.scene_models import (
    CrossSectionSceneModel,
    MaterialShape,
    PlacedLabel,
)


def cross_section_scene_model(
    scene_id: str,
    title: str,
    frame: ProcessFrame,
    profile: RenderProfile,
    render_intent: RenderIntent,
    filtered: FilteredStackGeometry,
    projection: RenderProjectionPlan,
    scene_bounds: tuple[float, float, float, float],
    shapes: tuple[MaterialShape, ...],
    labels: tuple[PlacedLabel, ...],
    simplify_annotations: tuple[dict[str, object], ...],
    measurement_annotations: tuple[MeasurementAnnotation, ...],
    warnings: tuple[str, ...],
    geometry_units: str = "um",
) -> CrossSectionSceneModel:
    """Assemble a backend-independent scene model from planned render parts."""

    physical_bounds = _physical_bounds(filtered)
    display_units = resolved_display_unit(
        _representative_thickness(shapes),
        geometry_units,
        render_intent.display_unit_preference,
    )
    return CrossSectionSceneModel(
        scene_id=scene_id,
        render_mode_id=profile.render_mode_id,
        title=title or scene_title(frame, profile),
        physical_units=display_units,
        visual_units="px",
        coordinate_frame=_coordinate_frame(filtered, scene_bounds, geometry_units, display_units),
        material_shapes=shapes,
        surface_profiles=(filtered.surface.points,),
        axes=_axes(profile, physical_bounds, geometry_units, display_units),
        scale_bars=scene_parts.scale_bars(
            profile, physical_bounds, geometry_units, display_units
        ),
        labels=labels,
        leaders=scene_parts.leaders(labels),
        callouts=scene_parts.callouts(labels),
        legend=scene_parts.legend(shapes, profile),
        annotations=scene_parts.step_annotations(frame, profile) + simplify_annotations
        + advanced_annotations(frame),
        measurement_annotations=measurement_annotations,
        highlights=scene_parts.highlights(render_intent) + advanced_highlights(frame),
        compression_metadata=projection.compression_metadata,
        warnings=warnings,
        source_refs=source_refs(frame, profile, render_intent),
    )


def _coordinate_frame(
    filtered: FilteredStackGeometry,
    scene_bounds: tuple[float, float, float, float],
    canonical_units: str,
    display_units: str,
) -> dict[str, object]:
    return {
        "physical_bounds": _physical_bounds(filtered),
        "canonical_units": "um",
        "source_units": canonical_units,
        "display_units": display_units,
        "visual_bounds": scene_bounds,
        "x_axis": "physical_linear",
        "z_axis": "up",
    }


def _axes(
    profile: RenderProfile,
    physical_bounds: tuple[float, float, float, float],
    canonical_units: str,
    display_units: str,
) -> tuple[dict[str, object], ...]:
    return scene_parts.axes(profile, physical_bounds, canonical_units, display_units)


def _physical_bounds(filtered: FilteredStackGeometry) -> tuple[float, float, float, float]:
    x_values = [column.x for column in filtered.geometry.columns] or [0.0, 1.0]
    z_values = [
        value
        for column in filtered.geometry.columns
        for interval in column.intervals
        for value in (interval.z_min, interval.z_max)
    ] or [0.0, 1.0]
    return (min(x_values), min(z_values), max(x_values), max(z_values))


def _representative_thickness(shapes: tuple[MaterialShape, ...]) -> float | None:
    visible = [
        abs(shape.physical_bounds[3] - shape.physical_bounds[1])
        for shape in shapes
        if shape.visible
    ]
    return min(visible) if visible else None
