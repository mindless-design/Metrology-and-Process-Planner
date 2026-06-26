"""End-to-end cross-section scene planning pipeline."""

from __future__ import annotations

from dataclasses import replace

from metrology_process_planner.domains.process import (
    CrossSectionProfile,
    Material,
    ProcessFrame,
    SolverResult,
    StackGeometry2D,
)
from metrology_process_planner.domains.session.display_units import resolved_display_unit
from metrology_process_planner.rendering.cross_section import scene_parts
from metrology_process_planner.rendering.cross_section.advanced_scene_metadata import (
    advanced_warnings,
)
from metrology_process_planner.rendering.cross_section.filtering import (
    FeatureFilter,
    FilterDiagnostics,
    FilteredStackGeometry,
)
from metrology_process_planner.rendering.cross_section.labels import (
    build_label_candidates,
    labels_have_collisions,
    place_labels,
)
from metrology_process_planner.rendering.cross_section.measurement_models import (
    MeasurementAnnotation,
)
from metrology_process_planner.rendering.cross_section.measurements import (
    build_measurement_annotations,
    measurement_warnings,
)
from metrology_process_planner.rendering.cross_section.models import RenderIntent, RenderProfile
from metrology_process_planner.rendering.cross_section.projection import (
    RenderProjectionPlan,
    build_render_projection,
)
from metrology_process_planner.rendering.cross_section.scene_builder import (
    cross_section_scene_model,
)
from metrology_process_planner.rendering.cross_section.scene_metadata import (
    unique_warning_codes,
)
from metrology_process_planner.rendering.cross_section.scene_models import (
    CrossSectionSceneModel,
    LabelCandidate,
    MaterialShape,
    PlacedLabel,
)
from metrology_process_planner.rendering.cross_section.simplification import (
    simplification_annotations,
    simplification_warnings,
)


def build_cross_section_scene(
    solver_result: SolverResult,
    profile: RenderProfile,
    intent: RenderIntent | None = None,
    materials: tuple[Material, ...] = (),
    scene_id: str = "cross-section",
    title: str = "",
) -> CrossSectionSceneModel:
    """Build a backend-independent scene from solver output and render intent."""

    if not solver_result.frames:
        return scene_parts.empty_scene(scene_id, profile, title, ("RENDER_FEATURE_FILTER_EMPTY",))
    render_intent = intent or RenderIntent.from_profile(profile)
    frame = _selected_frame(solver_result, render_intent)
    geometry = _geometry_from_profile(frame.profile)
    filtered = FeatureFilter().filter(geometry, render_intent, profile, materials)
    projection = build_render_projection(filtered.geometry, render_intent, materials)
    candidates = build_label_candidates(
        projection.shapes,
        render_intent.labeling_policy,
        render_intent.display_unit_preference,
    )
    scene_bounds = _visual_bounds(projection.shapes)
    labels = place_labels(
        candidates, projection.shapes, render_intent.labeling_policy, scene_bounds
    )
    shapes = _attach_candidates(projection.shapes, candidates)
    visual_warnings = _label_warnings(labels) + _shape_visual_warnings(shapes)
    simplify_annotations = simplification_annotations(
        profile.simplification_policy, filtered.diagnostics, shapes
    )
    simplify_warnings = simplification_warnings(
        profile.simplification_policy, filtered.diagnostics, shapes
    )
    measurement_annotations = _measurement_annotations(
        shapes,
        filtered,
        projection,
        solver_result,
        render_intent,
    )
    return cross_section_scene_model(
        scene_id, title, frame, profile, render_intent, filtered, projection, scene_bounds,
        shapes, labels, simplify_annotations, measurement_annotations,
        _scene_warnings(
            filtered, projection, visual_warnings, simplify_warnings, measurement_annotations, frame
        ),
        solver_result.units,
    )


def _measurement_annotations(
    shapes: tuple[MaterialShape, ...],
    filtered: FilteredStackGeometry,
    projection: RenderProjectionPlan,
    solver_result: SolverResult,
    render_intent: RenderIntent,
) -> tuple[MeasurementAnnotation, ...]:
    thicknesses = [
        abs(shape.physical_bounds[3] - shape.physical_bounds[1])
        for shape in shapes
        if shape.visible
    ]
    return build_measurement_annotations(
        shapes,
        (filtered.surface.points,),
        projection.compression_metadata,
        solver_result.units,
        resolved_display_unit(
            min(thicknesses) if thicknesses else None,
            solver_result.units,
            render_intent.display_unit_preference,
        ),
    )


def _label_warnings(labels: tuple[PlacedLabel, ...]) -> tuple[str, ...]:
    return ("RENDER_LABEL_COLLISION_UNRESOLVED",) if labels_have_collisions(labels) else ()


def _scene_warnings(
    filtered: FilteredStackGeometry,
    projection: RenderProjectionPlan,
    visual_warnings: tuple[str, ...],
    simplify_warnings: tuple[str, ...],
    measurement_annotations: tuple[MeasurementAnnotation, ...],
    frame: ProcessFrame,
) -> tuple[str, ...]:
    warnings = _warnings(filtered.diagnostics, projection.warnings, visual_warnings)
    return unique_warning_codes(
        warnings
        + simplify_warnings
        + measurement_warnings(measurement_annotations)
        + advanced_warnings(frame)
    )


def _shape_visual_warnings(shapes: tuple[MaterialShape, ...]) -> tuple[str, ...]:
    checks = (
        ("RENDER_THIN_LAYER_EXAGGERATED", _has_thin_or_exaggerated_shape),
        ("RENDER_COMPRESSION_APPLIED", _has_compressed_shape),
        ("RENDER_MATERIAL_OMITTED_BY_PROFILE", _has_hidden_shape),
    )
    return tuple(code for code, predicate in checks if predicate(shapes))


def _has_thin_or_exaggerated_shape(shapes: tuple[MaterialShape, ...]) -> bool:
    return any(shape.thin_layer_flag or shape.exaggerated_flag for shape in shapes)


def _has_compressed_shape(shapes: tuple[MaterialShape, ...]) -> bool:
    return any(shape.compressed_flag for shape in shapes)


def _has_hidden_shape(shapes: tuple[MaterialShape, ...]) -> bool:
    return any(not shape.visible for shape in shapes)


def _warnings(
    diagnostics: tuple[FilterDiagnostics, ...],
    projection_warnings: tuple[str, ...],
    label_warnings: tuple[str, ...],
) -> tuple[str, ...]:
    diagnostic_warnings = tuple(
        item.code for item in diagnostics if getattr(item, "severity", "info") != "info"
    )
    return tuple(dict.fromkeys(diagnostic_warnings + projection_warnings + label_warnings))


def _geometry_from_profile(profile: CrossSectionProfile) -> StackGeometry2D:
    return StackGeometry2D(profile.columns)


def _selected_frame(solver_result: SolverResult, intent: RenderIntent) -> ProcessFrame:
    if intent.selected_process_step_id:
        for frame in solver_result.frames:
            if frame.step_id == intent.selected_process_step_id:
                return frame
    return solver_result.frames[-1]


def _attach_candidates(
    shapes: tuple[MaterialShape, ...],
    candidates: tuple[LabelCandidate, ...],
) -> tuple[MaterialShape, ...]:
    by_target: dict[str, list[LabelCandidate]] = {}
    for candidate in candidates:
        by_target.setdefault(candidate.target_id, []).append(candidate)
    return tuple(replace(shape, label_candidates=tuple(by_target.get(shape.shape_id, ())))
                 for shape in shapes)


def _visual_bounds(shapes: tuple[MaterialShape, ...]) -> tuple[float, float, float, float]:
    if not shapes:
        return (0.0, 0.0, 1.0, 1.0)
    left = min(shape.visual_bounds[0] for shape in shapes)
    bottom = min(shape.visual_bounds[1] for shape in shapes)
    right = max(shape.visual_bounds[2] for shape in shapes)
    top = max(shape.visual_bounds[3] for shape in shapes)
    return (left, bottom, right, top)
