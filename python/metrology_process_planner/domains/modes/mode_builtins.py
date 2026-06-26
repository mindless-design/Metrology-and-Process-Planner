"""Built-in declarative session mode definitions."""

from __future__ import annotations

from metrology_process_planner.domains.modes.mode_non_process_builtins import non_process_modes
from metrology_process_planner.domains.modes.mode_output_policies import (
    ArtifactOutputDefinition,
    ArtifactPolicy,
    EditorPolicy,
    ProcessPolicy,
    ReportingPolicy,
)
from metrology_process_planner.domains.modes.mode_policies import (
    CaptureSequenceDefinition,
    MeasurementPolicy,
    MetadataFieldDefinition,
    MetadataSchema,
    ModeCapabilities,
    SetupDefinition,
)
from metrology_process_planner.domains.modes.mode_process_constants import (
    PROCESS_EDITOR_ACTIONS,
    PROCESS_EDITOR_GROUPS,
)
from metrology_process_planner.domains.modes.mode_process_flow import process_flow_summary_mode
from metrology_process_planner.domains.modes.mode_registry import ModeDefinition, ModeRegistry
from metrology_process_planner.domains.session.record import SessionMode


def built_in_mode_registry() -> ModeRegistry:
    """Return declarative definitions for built-in session modes."""

    return ModeRegistry(_core_modes() + _process_aware_modes())


def _core_modes() -> tuple[ModeDefinition, ...]:
    return non_process_modes() + (
        _process_aware_metrology_mode(),
        process_flow_summary_mode(),
    )


def _process_aware_modes() -> tuple[ModeDefinition, ...]:
    return (_profilometry_mode(), _ellipsometry_mode())


def _process_aware_metrology_mode() -> ModeDefinition:
    return ModeDefinition(
        SessionMode.PROCESS_AWARE_METROLOGY.value,
        "Process-Aware Metrology",
        family="process_aware",
        capabilities=ModeCapabilities(
            supports_measurements=True,
            supports_process_solver=True,
            supports_reporting=True,
        ),
        visible=False,
        capture=CaptureSequenceDefinition(supported_primitives=("site_box", "measurement")),
        measurements=MeasurementPolicy(enabled=True),
        artifacts=_process_artifacts("annotated_image", "process_summary"),
        process=ProcessPolicy("recommended", "none", ""),
        editor=_process_editor(("site_image", "annotated_image")),
        reporting=_process_reporting("capture_summary", "process_summary"),
    )


def _profilometry_mode() -> ModeDefinition:
    return ModeDefinition(
        SessionMode.PROFILOMETRY_PLANNER.value,
        "Profilometry Planner",
        family="process_aware",
        capabilities=ModeCapabilities(
            uses_setup_guide=True,
            supports_measurements=True,
            supports_process_solver=True,
            supports_reporting=True,
        ),
        setup=_process_setup(),
        capture=CaptureSequenceDefinition(
            primitive_type="site_then_line",
            supported_primitives=("site_then_line",),
            site_role="profilometry_site",
            inner_feature_type="line_capture",
            inner_feature_role="profilometry_line",
            inner_feature_kind="line",
            inner_feature_label="Line",
            child_canvas_object_type="profilometry_line",
            validators=("inside_parent_box",),
            saved_capture_type="site_plus_line",
            extension_key="profilometry",
            feature_id_field="line_feature_id",
            process_output_key="outputs",
            repeat_label_template="Profile Site {sequence:02d}",
        ),
        metadata=_metadata(
            "label",
            "notes",
            "line_label",
            "line_color",
            "line_weight_px",
            "text_scale",
            "target",
            "lsl",
            "usl",
        ),
        artifacts=_process_artifacts(
            "line_annotation",
            "profile_image",
            "cross_section_image",
            "full_stack_compressed_image",
        ),
        process=ProcessPolicy("recommended", "line_profile", "profilometry_surface_profile"),
        editor=_process_editor(("site_image", "line_annotation", "profile_image")),
        reporting=_process_reporting("profile_summary", "cross_section"),
    )


def _ellipsometry_mode() -> ModeDefinition:
    return ModeDefinition(
        SessionMode.ELLIPSOMETRY_PLANNER.value,
        "Ellipsometry Planner",
        family="process_aware",
        capabilities=ModeCapabilities(
            uses_setup_guide=True,
            supports_process_solver=True,
            supports_reporting=True,
        ),
        setup=_process_setup(),
        capture=CaptureSequenceDefinition(
            primitive_type="site_then_point",
            supported_primitives=("site_then_point",),
            site_role="ellipsometry_site",
            inner_feature_type="point_capture",
            inner_feature_role="ellipsometry_point",
            inner_feature_kind="point",
            inner_feature_label="Point",
            child_canvas_object_type="ellipsometry_point",
            validators=("inside_parent_box",),
            saved_capture_type="site_plus_point",
            extension_key="ellipsometry",
            feature_id_field="point_feature_id",
            process_output_key="point_stack",
            repeat_label_template="Film Site {sequence:02d}",
        ),
        metadata=_metadata("label", "point_label", "film_target", "notes"),
        artifacts=_process_artifacts(
            "point_annotation",
            "stack_image",
            "point_stack_table",
            "film_thickness_summary",
        ),
        process=ProcessPolicy("recommended", "point_stack", "point_stack_schematic"),
        editor=_process_editor(("site_image", "point_annotation", "stack_image")),
        reporting=_process_reporting("point_stack", "film_thickness_summary"),
    )

def _metadata(*field_ids: str) -> MetadataSchema:
    return MetadataSchema(tuple(MetadataFieldDefinition(field_id) for field_id in field_ids))


def _process_artifacts(annotation_role: str, *process_roles: str) -> ArtifactPolicy:
    return ArtifactPolicy(
        (
            ArtifactOutputDefinition("image", "site_image"),
            ArtifactOutputDefinition("layout_annotation", annotation_role),
            *(ArtifactOutputDefinition("process_output", role) for role in process_roles),
        )
    )


def _process_setup() -> SetupDefinition:
    return SetupDefinition(
        required=False,
        origin_policy="recommended",
        can_skip=True,
        stage_types=("source_layout", "coordinate_origin", "recipe_context"),
    )


def _process_editor(previews: tuple[str, ...]) -> EditorPolicy:
    return EditorPolicy(
        PROCESS_EDITOR_GROUPS,
        previews,
        PROCESS_EDITOR_ACTIONS,
        process_context_visible=True,
    )


def _process_reporting(*sections: str) -> ReportingPolicy:
    return ReportingPolicy(True, sections)
