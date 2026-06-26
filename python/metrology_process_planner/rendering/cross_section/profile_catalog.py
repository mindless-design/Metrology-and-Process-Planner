"""Built-in cross-section render profile catalog."""

from __future__ import annotations

from metrology_process_planner.rendering.cross_section.models import (
    CompressionPolicy,
    LabelPolicy,
    RenderProfile,
    ThinLayerPolicy,
)
from metrology_process_planner.rendering.cross_section.simplification import (
    RenderSimplificationPolicy,
)


def built_in_render_profiles() -> dict[str, RenderProfile]:
    """Return the supported built-in cross-section render profiles."""

    return {profile.profile_id: profile for profile in _profiles()}


def built_in_render_profile(profile_id: str) -> RenderProfile:
    """Return one built-in render profile by identifier."""

    profiles = built_in_render_profiles()
    if profile_id not in profiles:
        raise KeyError(f"Unknown render profile: {profile_id}")
    return profiles[profile_id]


def _profiles() -> tuple[RenderProfile, ...]:
    illustrative_compression = _illustrative_compression()
    thin = _thin_layer_policy()
    return (
        RenderProfile("physical_cross_section", "Physical cross-section",
                      "proportional_physical", "full_stack",
                      label_policy=LabelPolicy(), export_formats=("svg", "png")),
        RenderProfile("illustrative_process_cross_section", "Illustrative process cross-section",
                      "illustrative_process", "material_interfaces",
                      illustrative_compression, thin, _fib_simplification(),
                      LabelPolicy(show_step_labels=True), legend_policy="required"),
        RenderProfile("profilometry_surface_profile", "Profilometry surface profile",
                      "profilometry_surface", "surface_topography",
                      CompressionPolicy(False), ThinLayerPolicy(False),
                      _profilometry_simplification(),
                      LabelPolicy(show_thickness=True), legend_policy="compact"),
        RenderProfile("fib_full_stack_compressed", "FIB full-stack compressed",
                      "fib_full_stack_compressed", "full_stack",
                      _fib_compression(), thin, _fib_simplification(),
                      LabelPolicy(), legend_policy="required"),
        RenderProfile("process_flow_frame", "Process-flow frame",
                      "process_flow_frame", "current_step_change",
                      illustrative_compression, thin, _process_flow_simplification(),
                      LabelPolicy(show_step_labels=True), legend_policy="compact"),
        RenderProfile("point_stack_schematic", "Point stack schematic",
                      "point_stack_schematic", "local_point_stack",
                      CompressionPolicy(False), thin, RenderSimplificationPolicy(),
                      LabelPolicy(mode="leader_labels"), legend_policy="required"),
    )


def _illustrative_compression() -> CompressionPolicy:
    return CompressionPolicy(
        True, preserve_top_n_nm=750.0, min_visual_thickness_px=2.0,
        max_compression_ratio=30.0, show_break_marks=True, show_compression_legend=True,
    )


def _fib_compression() -> CompressionPolicy:
    return CompressionPolicy(
        True, preserve_top_n_nm=1000.0, min_visual_thickness_px=2.0,
        max_compression_ratio=100.0, show_break_marks=True, show_compression_legend=True,
    )


def _thin_layer_policy() -> ThinLayerPolicy:
    return ThinLayerPolicy(
        True, min_visual_thickness_px=12.0, max_exaggeration_ratio=25.0,
        prefer_callout_when_too_thin=True, show_exaggeration_note=True,
        conformal_outline_emphasis=True,
        critical_material_categories=("liner", "etch_stop", "passivation"),
    )


def _profilometry_simplification() -> RenderSimplificationPolicy:
    return RenderSimplificationPolicy(
        True, hide_irrelevant_buried_layers=True, simplify_tiny_slivers=True,
        preserve_surface_profile=True,
    )


def _fib_simplification() -> RenderSimplificationPolicy:
    return RenderSimplificationPolicy(
        True, remove_redundant_regions=True, merge_same_material_runs=True,
        preserve_critical_thin_layers=True,
    )


def _process_flow_simplification() -> RenderSimplificationPolicy:
    return RenderSimplificationPolicy(
        True, remove_redundant_regions=True, simplify_tiny_slivers=True,
        preserve_selected_feature_context=True,
    )
