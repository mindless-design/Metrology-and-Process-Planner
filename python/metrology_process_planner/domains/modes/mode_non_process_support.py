"""Shared constructors for recipe-free mode definitions."""

from __future__ import annotations

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
    MetadataSchema,
    ModeCapabilities,
    SetupDefinition,
)
from metrology_process_planner.domains.modes.mode_registry import ModeDefinition
from metrology_process_planner.domains.session.record import SessionMode

NON_PROCESS_EDITOR_ACTIONS = (
    "pending_save",
    "pending_retake",
    "pending_discard",
    "add_measurement",
    "regenerate_artifact",
    "export_csv",
    "build_powerpoint",
)


def non_process_mode(
    mode: SessionMode,
    label: str,
    primitives: tuple[str, ...] = ("site_box",),
    family: str = "generic_capture",
    supports_measurements: bool = False,
    supports_batch_capture: bool = False,
    supports_grid_datasets: bool = False,
    uses_setup_guide: bool = False,
    setup: SetupDefinition | None = None,
    capture: CaptureSequenceDefinition | None = None,
    metadata: MetadataSchema | None = None,
    artifacts: ArtifactPolicy | None = None,
    editor: EditorPolicy | None = None,
    reporting_sections: tuple[str, ...] = (),
) -> ModeDefinition:
    """Return a mode with recipe, solver, and process context disabled."""

    return ModeDefinition(
        mode.value,
        label,
        family=family,
        capabilities=ModeCapabilities(
            uses_setup_guide=uses_setup_guide,
            supports_measurements=supports_measurements,
            supports_grid_datasets=supports_grid_datasets,
            supports_reporting=True,
            supports_batch_capture=supports_batch_capture,
        ),
        setup=setup or SetupDefinition(),
        capture=capture or CaptureSequenceDefinition(supported_primitives=primitives),
        metadata=metadata or MetadataSchema(),
        measurements=MeasurementPolicy(enabled=supports_measurements),
        artifacts=artifacts or capture_artifacts(),
        process=ProcessPolicy("forbidden", "none", ""),
        editor=editor or non_process_editor(
            ("dashboard", "pending", "captures", "measurements", "reports", "warnings")
        ),
        reporting=ReportingPolicy(
            True,
            ("capture_summary", "measurements", *reporting_sections),
        ),
    )


def capture_artifacts(annotation_role: str = "annotated_image") -> ArtifactPolicy:
    """Return the default non-process capture artifact policy."""

    return ArtifactPolicy(
        (
            ArtifactOutputDefinition("image", "site_image", required=True),
            ArtifactOutputDefinition("layout_annotation", annotation_role),
            ArtifactOutputDefinition("measurement_detail", "measurement_detail"),
        )
    )


def non_process_editor(
    groups: tuple[str, ...],
    previews: tuple[str, ...] = ("site_image", "annotated_image", "measurement_detail"),
) -> EditorPolicy:
    """Return editor policy without recipe or solver actions."""

    return EditorPolicy(
        groups,
        previews,
        NON_PROCESS_EDITOR_ACTIONS,
        process_context_visible=False,
    )
