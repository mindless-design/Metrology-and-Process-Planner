"""Cross-section rendering pipeline contracts and planners."""

from metrology_process_planner.rendering.cross_section.artifacts import (
    RENDER_WARNING_CODES,
    build_failed_render_warning,
    build_render_artifact_record,
)
from metrology_process_planner.rendering.cross_section.backend import (
    CrossSectionRenderer,
    SvgCrossSectionRenderer,
)
from metrology_process_planner.rendering.cross_section.filtering import (
    FeatureFilter,
    FilterDiagnostics,
    FilteredFeatureSet,
    FilteredStackGeometry,
)
from metrology_process_planner.rendering.cross_section.labels import (
    build_label_candidates,
    place_labels,
)
from metrology_process_planner.rendering.cross_section.models import (
    CompressionPolicy,
    CrossSectionOutputSpec,
    CrossSectionRenderResult,
    LabelPolicy,
    RenderIntent,
    RenderProfile,
    ThinLayerPolicy,
    VisualTransform,
)
from metrology_process_planner.rendering.cross_section.pipeline import (
    build_cross_section_scene,
)
from metrology_process_planner.rendering.cross_section.process_flow import build_process_flow_scenes
from metrology_process_planner.rendering.cross_section.profile_catalog import (
    built_in_render_profile,
    built_in_render_profiles,
)
from metrology_process_planner.rendering.cross_section.profile_defaults import (
    PROCESS_ROLE_RENDER_PROFILES,
    RenderProfileResolution,
    default_render_profile_id,
    resolve_render_profile,
)
from metrology_process_planner.rendering.cross_section.projection import (
    RenderProjectionPlan,
    build_render_projection,
)
from metrology_process_planner.rendering.cross_section.scene_models import (
    CompressionMetadata,
    CrossSectionSceneModel,
    LabelCandidate,
    LegendEntry,
    LegendModel,
    MaterialShape,
    PlacedLabel,
    scene_from_dict,
    scene_to_dict,
)
from metrology_process_planner.rendering.cross_section.simplification import (
    RenderSimplificationPolicy,
)

__all__ = [
    "CompressionMetadata",
    "CompressionPolicy",
    "CrossSectionOutputSpec",
    "CrossSectionRenderResult",
    "CrossSectionRenderer",
    "CrossSectionSceneModel",
    "FeatureFilter",
    "FilterDiagnostics",
    "FilteredFeatureSet",
    "FilteredStackGeometry",
    "LabelCandidate",
    "LabelPolicy",
    "LegendEntry",
    "LegendModel",
    "MaterialShape",
    "PlacedLabel",
    "PROCESS_ROLE_RENDER_PROFILES",
    "RENDER_WARNING_CODES",
    "RenderIntent",
    "RenderProfile",
    "RenderProfileResolution",
    "RenderProjectionPlan",
    "RenderSimplificationPolicy",
    "SvgCrossSectionRenderer",
    "ThinLayerPolicy",
    "VisualTransform",
    "build_cross_section_scene",
    "build_failed_render_warning",
    "build_label_candidates",
    "build_process_flow_scenes",
    "build_render_artifact_record",
    "build_render_projection",
    "built_in_render_profile",
    "built_in_render_profiles",
    "default_render_profile_id",
    "place_labels",
    "resolve_render_profile",
    "scene_from_dict",
    "scene_to_dict",
]
