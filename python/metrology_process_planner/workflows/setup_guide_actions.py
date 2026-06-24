"""Setup-guide active-state and command resolution."""

from __future__ import annotations

from metrology_process_planner.domains.session import SessionRecord
from metrology_process_planner.workflows.setup_guide_models import (
    SetupGuideAction,
    SetupGuideState,
    SetupStageSnapshot,
    SetupStageStatus,
)


def active_stage(stages: tuple[SetupStageSnapshot, ...]) -> SetupStageSnapshot:
    """Return the first unresolved setup stage."""

    for stage in stages:
        if stage.status not in (SetupStageStatus.COMPLETE, SetupStageStatus.SKIPPED):
            return stage
    return stages[-1]


def guide_state(active: SetupStageSnapshot, session: SessionRecord) -> SetupGuideState:
    """Return the top-level guide state for the active card."""

    if session.setup.is_capture_ready:
        return SetupGuideState.SETUP_READY
    if active.status is SetupStageStatus.WARNING and active.stage_type == "recipe_select":
        return SetupGuideState.RECIPE_WARNING
    if active.status is SetupStageStatus.BLOCKED:
        return SetupGuideState.BLOCKED
    return _STATE_BY_STAGE_TYPE.get(active.stage_type, SetupGuideState.COORDINATE_MODE_REQUIRED)


def available_actions(
    active: SetupStageSnapshot,
    stages: tuple[SetupStageSnapshot, ...],
) -> tuple[SetupGuideAction, ...]:
    """Return command intents for the current guide state."""

    actions = []
    if active.primary_action is not None:
        actions.append(active.primary_action)
    actions.extend(active.secondary_actions)
    actions.append(SetupGuideAction("ReturnToEditor", "Return to Editor"))
    actions.append(SetupGuideAction("CloseSetupGuide", "Close"))
    return _dedupe_actions(actions, stages)


def status_message(active: SetupStageSnapshot) -> str:
    """Return a compact status message for the active setup card."""

    if active.status is SetupStageStatus.WARNING:
        return f"{active.label} needs attention."
    if active.status is SetupStageStatus.BLOCKED:
        return f"{active.label} is blocked until prior setup is complete."
    return active.description or active.label


def _dedupe_actions(
    actions: list[SetupGuideAction],
    stages: tuple[SetupStageSnapshot, ...],
) -> tuple[SetupGuideAction, ...]:
    seen: set[str] = set()
    deduped = []
    for action in actions:
        if action.command_id not in seen:
            deduped.append(action)
        seen.add(action.command_id)
    if any(stage.stage_type == "origin_point_capture" for stage in stages):
        deduped.append(SetupGuideAction("StartOriginCapture", "Start Origin Capture"))
    return tuple(deduped)


_STATE_BY_STAGE_TYPE = {
    "origin_choice": SetupGuideState.COORDINATE_MODE_REQUIRED,
    "origin_point_capture": SetupGuideState.ORIGIN_POINT_REQUIRED,
    "origin_reference_box_capture": SetupGuideState.ORIGIN_REFERENCE_OPTIONAL,
    "alignment_box_capture": SetupGuideState.ALIGNMENT_REQUIRED,
    "sem_alignment_box_capture": SetupGuideState.ALIGNMENT_REQUIRED,
    "recipe_select": SetupGuideState.RECIPE_REQUIRED,
    "recipe_validate": SetupGuideState.RECIPE_REQUIRED,
}
