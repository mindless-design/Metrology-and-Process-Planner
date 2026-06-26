"""Setup inspector-field helpers for the unified editor."""

from __future__ import annotations

from metrology_process_planner.domains.session import (
    ModeRegistry,
    SessionRecord,
    built_in_mode_registry,
)
from metrology_process_planner.workflows.editor.builder_setup_artifacts import setup_artifact_refs
from metrology_process_planner.workflows.editor.view_models import MetadataField
from metrology_process_planner.workflows.setup_guide_models import SetupStageSnapshot
from metrology_process_planner.workflows.setup_guide_requirements import (
    incomplete_required_setup_labels,
)
from metrology_process_planner.workflows.setup_guide_stages import setup_stages


def setup_fields(
    session: SessionRecord,
    mode_registry: ModeRegistry | None = None,
) -> tuple[MetadataField, ...]:
    """Return compact setup state fields for the selected setup item."""

    mode = (mode_registry or built_in_mode_registry()).definition(session.mode.value)
    stages = setup_stages(session, mode, mode_registry)
    incomplete = incomplete_required_setup_labels(session, mode)
    completed = _completed_stage_count(stages)
    artifact_count = _setup_artifact_count(session, mode_registry)
    return (
        MetadataField("mode", "Mode", session.mode.value, read_only=True),
        MetadataField(
            "setup_status",
            "Setup Status",
            _setup_status(session, incomplete),
            read_only=True,
        ),
        MetadataField(
            "current_stage",
            "Current Stage",
            _current_stage_label(stages),
            read_only=True,
        ),
        MetadataField(
            "completed_stages",
            "Completed Stages",
            str(completed),
            read_only=True,
        ),
        MetadataField(
            "required_incomplete",
            "Required Incomplete",
            ", ".join(incomplete),
            read_only=True,
        ),
        MetadataField(
            "setup_artifacts",
            "Setup Artifacts",
            str(artifact_count),
            read_only=True,
        ),
    )


def _setup_status(session: SessionRecord, incomplete: tuple[str, ...]) -> str:
    return "ready" if session.setup.is_capture_ready and not incomplete else "incomplete"


def _completed_stage_count(stages: tuple[SetupStageSnapshot, ...]) -> int:
    return sum(1 for stage in stages if stage.status.value == "complete")


def _setup_artifact_count(
    session: SessionRecord,
    mode_registry: ModeRegistry | None,
) -> int:
    return len(setup_artifact_refs(session, mode_registry))


def _current_stage_label(stages: tuple[SetupStageSnapshot, ...]) -> str:
    for stage in stages:
        if stage.status.value in {"active", "blocked", "not_started"}:
            return stage.label
    return "Ready for Capture" if stages else "not required"
