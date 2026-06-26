"""Render intent, profile, transform, and output contracts."""

from __future__ import annotations

from dataclasses import dataclass, replace
from typing import Any, Optional

from metrology_process_planner.rendering.cross_section.simplification import (
    RenderSimplificationPolicy,
)


@dataclass(frozen=True)
class CompressionPolicy:
    """Rules for compressing physically large regions in render space."""

    enabled: bool = False
    target_visual_height_px: int = 620
    compress_material_categories: tuple[str, ...] = ()
    compress_material_ids: tuple[str, ...] = ()
    preserve_material_ids: tuple[str, ...] = ()
    preserve_top_n_nm: float = 0.0
    min_visual_thickness_px: float = 1.0
    max_compression_ratio: float = 50.0
    show_break_marks: bool = False
    show_compression_legend: bool = False


@dataclass(frozen=True)
class ThinLayerPolicy:
    """Rules for making physically thin layers readable without hiding distortion."""

    enabled: bool = False
    min_visual_thickness_px: float = 2.0
    affected_material_ids: tuple[str, ...] = ()
    affected_categories: tuple[str, ...] = ()
    max_exaggeration_ratio: float = 20.0
    prefer_callout_when_too_thin: bool = True
    show_exaggeration_note: bool = False
    conformal_outline_emphasis: bool = False
    group_adjacent_thin_layers: bool = True
    critical_material_ids: tuple[str, ...] = ()
    critical_material_categories: tuple[str, ...] = ()

    @property
    def prefer_leader_when_too_thin(self) -> bool:
        """Compatibility alias using the product language for leader callouts."""

        return self.prefer_callout_when_too_thin


@dataclass(frozen=True)
class LabelPolicy:
    """Declarative label placement behavior for a cross-section scene."""

    mode: str = "hybrid_auto"
    show_material_labels: bool = True
    show_step_labels: bool = False
    show_thickness: bool = True
    allow_inline: bool = True
    allow_leaders: bool = True
    allow_callouts: bool = True
    allow_legend_only: bool = True


@dataclass(frozen=True)
class RenderProfile:
    """Named render behavior used by modes, sessions, reports, and exports."""

    profile_id: str
    display_name: str
    render_mode_id: str
    feature_filter_policy: str
    compression_policy: CompressionPolicy = CompressionPolicy()
    thin_layer_policy: ThinLayerPolicy = ThinLayerPolicy()
    simplification_policy: RenderSimplificationPolicy = RenderSimplificationPolicy()
    label_policy: LabelPolicy = LabelPolicy()
    color_policy: str = "material_colors"
    axis_policy: str = "physical_ticks"
    display_unit_preference: str = "auto"
    legend_policy: str = "visible_materials"
    theme_id: str = "engineering_dark"
    output_size: tuple[int, int] = (1200, 720)
    export_formats: tuple[str, ...] = ("svg", "png")


@dataclass(frozen=True)
class RenderIntent:
    """One request to turn solver geometry into visual communication."""

    mode_id: str
    purpose: str
    selected_site_id: str = ""
    selected_feature_id: str = ""
    selected_process_step_id: Optional[str] = None
    focus_policy: str = "full_stack"
    stack_inclusion_policy: str = "include_all_materials"
    compression_policy: CompressionPolicy = CompressionPolicy()
    exaggeration_policy: ThinLayerPolicy = ThinLayerPolicy()
    labeling_policy: LabelPolicy = LabelPolicy()
    axis_policy: str = "physical_ticks"
    display_unit_preference: str = "auto"
    legend_policy: str = "visible_materials"
    highlight_policy: str = ""
    output_context: str = "preview"

    @classmethod
    def from_profile(cls, profile: RenderProfile, **overrides: Any) -> RenderIntent:
        """Build intent defaults from a declarative render profile."""

        base = cls(
            mode_id=profile.render_mode_id,
            purpose=profile.display_name,
            focus_policy=profile.feature_filter_policy,
            stack_inclusion_policy=_stack_policy(profile.feature_filter_policy),
            compression_policy=profile.compression_policy,
            exaggeration_policy=profile.thin_layer_policy,
            labeling_policy=profile.label_policy,
            axis_policy=profile.axis_policy,
            display_unit_preference=profile.display_unit_preference,
            legend_policy=profile.legend_policy,
        )
        return base if not overrides else _with_overrides(base, overrides)


@dataclass(frozen=True)
class VisualTransform:
    """Physical-to-visual mapping metadata for render projections."""

    x_transform: str = "physical_linear"
    z_transform: str = "physical_linear"
    material_overrides: dict[str, str] | None = None
    min_visual_thickness: float = 0.0
    max_visual_thickness: float = 0.0
    compression_regions: tuple[tuple[float, float], ...] = ()
    break_marks: tuple[tuple[float, float], ...] = ()
    exaggeration_annotations: tuple[str, ...] = ()
    mapping_physical_to_visual: tuple[tuple[float, float], ...] = ()


@dataclass(frozen=True)
class CrossSectionOutputSpec:
    """Backend-independent output request for cross-section rendering."""

    width_px: int = 1200
    height_px: int = 720
    dpi: int = 150
    background: str = "#ffffff"
    transparent: bool = False
    font_policy: str = "default"
    theme_id: str = "engineering_dark"
    margins: tuple[int, int, int, int] = (56, 36, 180, 56)
    target_context: str = "preview"
    output_path: str = ""
    artifact_id: str = ""


@dataclass(frozen=True)
class CrossSectionRenderResult:
    """Result metadata returned by a concrete cross-section renderer."""

    artifact_id: str
    path: str
    width_px: int
    height_px: int
    status: str
    warnings: tuple[str, ...] = ()
    render_metadata: dict[str, object] | None = None


def _stack_policy(filter_policy: str) -> str:
    if filter_policy == "surface_topography":
        return "include_surface_affecting_only"
    if filter_policy == "current_step_change":
        return "include_materials_until_step"
    return "include_all_materials"


def _with_overrides(intent: RenderIntent, overrides: dict[str, Any]) -> RenderIntent:
    return replace(intent, **overrides)
