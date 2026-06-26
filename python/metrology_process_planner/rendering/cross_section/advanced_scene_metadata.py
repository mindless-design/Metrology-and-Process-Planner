"""Advanced projection metadata conversion for cross-section scenes."""

from __future__ import annotations

from metrology_process_planner.domains.process import ProcessFrame
from metrology_process_planner.solver.geometry_models import RenderProjection


def advanced_annotations(frame: ProcessFrame) -> tuple[dict[str, object], ...]:
    """Return scene annotations from public render projection metadata."""

    projection = frame.render_projection or frame.projection
    if projection is None:
        return ()
    return (
        *_conformal_annotations(projection),
        *_tapered_annotations(projection),
        *_undercut_annotations(projection),
    )


def advanced_highlights(frame: ProcessFrame) -> tuple[dict[str, object], ...]:
    """Return visual markers from public render projection metadata."""

    projection = frame.render_projection or frame.projection
    if projection is None:
        return ()
    return (
        *_pinch_off_highlights(projection),
        *_void_highlights(projection),
        *_seam_highlights(projection),
    )


def advanced_warnings(frame: ProcessFrame) -> tuple[str, ...]:
    """Return render warning codes implied by advanced projection metadata."""

    projection = frame.render_projection or frame.projection
    if projection is None:
        return ()
    codes: list[str] = []
    if projection.pinch_off_regions:
        codes.append("RENDER_PINCH_OFF_MARKER_PRESENT")
    if projection.tapered_regions:
        codes.append("RENDER_TAPERED_SIDEWALL_METADATA_PRESENT")
    if projection.conformal_layers and projection.thin_layer_hints.get(
        "exaggeration_note_required"
    ):
        codes.append("RENDER_CONFORMAL_THIN_LAYER_HINT_PRESENT")
    return tuple(codes)


def _conformal_annotations(projection: RenderProjection) -> tuple[dict[str, object], ...]:
    return tuple(
        {
            "kind": "conformal_layer",
            "material_id": layer.material_id,
            "step_id": layer.source_step_id,
            "physical_thickness": layer.physical_thickness,
            "coverage_factors": {
                "top": layer.top_coverage_factor,
                "sidewall": layer.sidewall_coverage_factor,
                "bottom": layer.bottom_coverage_factor,
            },
            "thin_layer_flag": layer.thin_layer_flag,
            "approximation": layer.approximation,
        }
        for layer in projection.conformal_layers
    )


def _tapered_annotations(projection: RenderProjection) -> tuple[dict[str, object], ...]:
    return tuple(
        {
            "kind": "tapered_region",
            "step_id": region.source_step_id,
            "polygon": region.polygon,
            "sidewall_angle_deg": region.sidewall_angle_deg,
            "target_materials": region.target_materials,
            "stop_materials": region.stop_materials,
        }
        for region in projection.tapered_regions
    )


def _undercut_annotations(projection: RenderProjection) -> tuple[dict[str, object], ...]:
    return tuple(
        {
            "kind": "undercut_region",
            "step_id": region.source_step_id,
            "bounds": (region.x_min, region.z_min, region.x_max, region.z_max),
            "etch_distance": region.etch_distance,
            "target_materials": region.target_materials,
        }
        for region in projection.undercut_regions
    )


def _pinch_off_highlights(projection: RenderProjection) -> tuple[dict[str, object], ...]:
    return tuple(
        {
            "kind": "pinch_off_warning",
            "step_id": region.source_step_id,
            "bounds": (region.x_min, region.z_min, region.x_max, region.z_max),
            "gap_width": region.gap_width,
        }
        for region in projection.pinch_off_regions
    )


def _void_highlights(projection: RenderProjection) -> tuple[dict[str, object], ...]:
    return tuple(
        {
            "kind": "void_marker",
            "step_id": region.source_step_id,
            "bounds": (region.x_min, region.z_min, region.x_max, region.z_max),
        }
        for region in projection.void_regions
    )


def _seam_highlights(projection: RenderProjection) -> tuple[dict[str, object], ...]:
    return tuple(
        {
            "kind": "seam_marker",
            "step_id": region.source_step_id,
            "bounds": (region.x, region.z_min, region.x, region.z_max),
        }
        for region in projection.seam_regions
    )
