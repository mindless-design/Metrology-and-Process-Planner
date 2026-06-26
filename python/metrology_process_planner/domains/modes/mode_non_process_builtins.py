"""Built-in recipe-free capture and metrology mode definitions."""

from __future__ import annotations

from dataclasses import replace

from metrology_process_planner.domains.measurement.records import (
    EDGE_CONVENTION_OPTIONS,
    MEASUREMENT_TYPE_OPTIONS,
)
from metrology_process_planner.domains.modes.mode_grid_builtin import grid_measurement_mode
from metrology_process_planner.domains.modes.mode_non_process_support import (
    capture_artifacts,
    non_process_editor,
    non_process_mode,
)
from metrology_process_planner.domains.modes.mode_non_process_vocab import (
    CAD_REVIEW_CATEGORIES,
    CAD_REVIEW_SEVERITIES,
    CDSEM_FEATURE_TYPES,
)
from metrology_process_planner.domains.modes.mode_policies import (
    CaptureSequenceDefinition,
    MetadataFieldDefinition,
    MetadataSchema,
    SetupDefinition,
)
from metrology_process_planner.domains.modes.mode_registry import ModeDefinition
from metrology_process_planner.domains.session.record import SessionMode

SETUP_EDITOR_GROUPS = (
    "dashboard", "setup", "pending", "captures", "measurements", "reports", "warnings",
)

def non_process_modes() -> tuple[ModeDefinition, ...]:
    """Return built-in modes that must not expose recipe or solver context."""

    return (
        _simple_labeled_capture_mode(),
        _hidden_alias(
            _simple_labeled_capture_mode(),
            SessionMode.SIMPLE_LABELED_CAPTURE,
            "Alias for Simple Labeled Capture; canonical sessions still use simple_capture.",
        ),
        _fast_batch_capture_mode(),
        _cad_review_mode(),
        _hidden_alias(
            _cad_review_mode(),
            SessionMode.CAD_REVIEW_CAPTURE,
            "Alias for CAD Review Capture; canonical sessions still use cad_review.",
        ),
        _optical_metrology_mode(),
        replace(
            _cdsem_measurement_mode(SessionMode.CDSEM_CAPTURE),
            visible=False,
            category="legacy",
            description="Legacy alias; load existing sessions but hide from new-session pickers.",
        ),
        _cdsem_measurement_mode(SessionMode.CDSEM_MEASUREMENT),
        replace(
            _cdsem_measurement_mode(SessionMode.CDSEM_PLANNING),
            visible=False,
            category="alias",
            description=(
                "Planning alias for CDSEM Measurement; load existing planning sessions "
                "without adding a duplicate operator mode."
            ),
        ),
        grid_measurement_mode(),
    )


def _hidden_alias(
    definition: ModeDefinition,
    alias: SessionMode,
    description: str,
) -> ModeDefinition:
    return replace(
        definition,
        mode_id=alias.value,
        visible=False,
        category="alias",
        description=description,
    )


def _simple_labeled_capture_mode() -> ModeDefinition:
    return non_process_mode(
        SessionMode.SIMPLE_CAPTURE,
        "Simple Labeled Capture",
        supports_measurements=True,
        metadata=_metadata("label", "notes", "capture_role", "capture_type", "tags"),
    )


def _fast_batch_capture_mode() -> ModeDefinition:
    return non_process_mode(
        SessionMode.FAST_BATCH_CAPTURE,
        "Fast Batch Capture",
        supports_measurements=True,
        supports_batch_capture=True,
        capture=CaptureSequenceDefinition(
            review=False,
            repeat_label_template="Capture {sequence:03d}",
        ),
        metadata=_metadata("label", "notes", "capture_role", "tags"),
    )


def _cad_review_mode() -> ModeDefinition:
    return non_process_mode(
        SessionMode.CAD_REVIEW,
        "CAD Review Capture",
        family="review",
        supports_measurements=True,
        metadata=_metadata(
            "label",
            _field(
                "review_category",
                "Review Category",
                default="layout_issue",
                options=CAD_REVIEW_CATEGORIES,
            ),
            _field("severity", "Severity", default="medium", options=CAD_REVIEW_SEVERITIES),
            "notes",
            "tags",
            _field("owner", "Owner / Assignee"),
        ),
        artifacts=capture_artifacts("review_annotation"),
    )


def _optical_metrology_mode() -> ModeDefinition:
    return non_process_mode(
        SessionMode.OPTICAL_METROLOGY,
        "Optical Metrology",
        ("site_box", "point"),
        family="metrology",
        supports_measurements=True,
        uses_setup_guide=True,
        setup=_metrology_setup(
            "origin_choice",
            "optional_origin_point",
            "optional_origin_reference_image",
            "required_optical_alignment_mark",
            "ready_for_capture",
        ),
        metadata=_metadata("label", "notes", "capture_role", "tags"),
        artifacts=capture_artifacts("measurement_annotation"),
        editor=non_process_editor(SETUP_EDITOR_GROUPS),
    )


def _cdsem_measurement_mode(mode: SessionMode) -> ModeDefinition:
    return non_process_mode(
        mode,
        "CDSEM Measurement",
        family="metrology",
        supports_measurements=True,
        uses_setup_guide=True,
        setup=_metrology_setup(
            "origin_choice",
            "optional_origin_reference_image",
            "required_optical_alignment_mark",
            "required_sem_alignment_mark",
            "ready_for_capture",
        ),
        metadata=_metadata(
            "label",
            _field(
                "feature_type",
                "Feature Type",
                required=True,
                default="line",
                options=CDSEM_FEATURE_TYPES,
            ),
            _field(
                "measurement_type",
                "Measurement Type",
                default="cd",
                options=MEASUREMENT_TYPE_OPTIONS,
            ),
            "target",
            "lsl",
            "usl",
            _field(
                "edge_convention",
                "Edge Convention",
                default="outer_edges",
                options=EDGE_CONVENTION_OPTIONS,
            ),
            "notes",
        ),
        artifacts=capture_artifacts("measurement_annotation"),
        editor=non_process_editor(SETUP_EDITOR_GROUPS),
    )


def _metadata(*fields: str | MetadataFieldDefinition) -> MetadataSchema:
    return MetadataSchema(
        tuple(
            field if isinstance(field, MetadataFieldDefinition) else _field(field)
            for field in fields
        )
    )


def _field(field_id: str, label: str = "", field_type: str = "text",
           required: bool = False, default: str = "",
           options: tuple[str, ...] = ()) -> MetadataFieldDefinition:
    return MetadataFieldDefinition(field_id, label, field_type, required, default, options)


def _metrology_setup(*stage_types: str) -> SetupDefinition:
    return SetupDefinition(required=True, can_skip=False, stage_types=stage_types)
