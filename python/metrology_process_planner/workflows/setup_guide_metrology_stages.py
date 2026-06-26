"""Setup-guide stages for recipe-free metrology modes."""

from __future__ import annotations

from metrology_process_planner.domains.session import SessionRecord
from metrology_process_planner.workflows.setup_guide_models import (
    SetupGuideAction,
    SetupStageSnapshot,
    SetupStageStatus,
)
from metrology_process_planner.workflows.setup_guide_workflow_status import (
    workflow_stage_status,
)


def origin_choice_stage(session: SessionRecord) -> SetupStageSnapshot:
    """Return the coordinate-mode setup card."""

    return SetupStageSnapshot(
        "origin_choice",
        "origin_choice",
        "Coordinate Mode",
        SetupStageStatus.COMPLETE if session.setup.coordinate_mode else SetupStageStatus.ACTIVE,
        required=True,
        description="Choose global or origin-relative coordinates.",
        primary_action=SetupGuideAction("UseGlobalCoordinates", "Use Global Coordinates"),
        secondary_actions=(SetupGuideAction("UseOriginCoordinates", "Use Origin Coordinates"),),
    )


def origin_reference_stage(session: SessionRecord) -> SetupStageSnapshot:
    """Return the optional origin-reference capture setup card."""

    stage_type = "origin_reference_box_capture"
    status = _item_status(session, "origin_reference", SetupStageStatus.NOT_STARTED)
    return SetupStageSnapshot(
        "origin_reference",
        stage_type,
        "Origin Reference Image",
        workflow_stage_status(session, stage_type, status),
        required=False,
        description="Capture an optional reference image for the chosen origin.",
        primary_action=SetupGuideAction(
            "StartOriginReferenceCapture",
            "Start Origin Reference Capture",
        ),
        secondary_actions=(SetupGuideAction("SkipOptionalSetupStage", "Skip"),),
    )


def alignment_mark_stage(
    session: SessionRecord,
    stage_id: str,
    stage_type: str,
    label: str,
    command_id: str,
    command_label: str,
) -> SetupStageSnapshot:
    """Return a required alignment-mark setup card."""

    status = _item_status(session, stage_id, SetupStageStatus.ACTIVE)
    return SetupStageSnapshot(
        stage_id,
        stage_type,
        label,
        workflow_stage_status(session, stage_type, status),
        required=True,
        description=f"Capture the required {label.lower()}.",
        primary_action=SetupGuideAction(command_id, command_label),
        requirement_badge="required",
    )


def _item_status(
    session: SessionRecord,
    item_id: str,
    default: SetupStageStatus,
) -> SetupStageStatus:
    for item in session.setup.items:
        if item.id == item_id:
            return _status_from_text(item.status)
    return default


def _status_from_text(value: str) -> SetupStageStatus:
    normalized = value.strip().lower()
    for status in SetupStageStatus:
        if status.value == normalized:
            return status
    if normalized in {"ready", "done"}:
        return SetupStageStatus.COMPLETE
    if normalized in {"pending", ""}:
        return SetupStageStatus.NOT_STARTED
    return SetupStageStatus.ACTIVE
