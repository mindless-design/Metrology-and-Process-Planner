"""Explicit setup-guide workflow state machine."""

from __future__ import annotations

from dataclasses import replace

from metrology_process_planner.domains.session import ModeDefinition, ModeRegistry, SessionRecord
from metrology_process_planner.workflows.setup_guide_actions import (
    active_stage,
    available_actions,
    guide_state,
    status_message,
)
from metrology_process_planner.workflows.setup_guide_models import (
    SetupGuideAction,
    SetupGuideSnapshot,
    SetupGuideState,
    SetupStageSnapshot,
    SetupStageStatus,
)
from metrology_process_planner.workflows.setup_guide_requirements import (
    incomplete_required_setup_labels,
)
from metrology_process_planner.workflows.setup_guide_stages import setup_stages


class SetupGuideStateMachine:
    """Resolve setup-guide state from canonical session and mode policy."""

    def evaluate(
        self,
        session: SessionRecord | None,
        mode: ModeDefinition | None = None,
        mode_registry: ModeRegistry | None = None,
    ) -> SetupGuideSnapshot:
        """Return a deterministic setup-guide snapshot."""

        if session is None:
            return _session_required_snapshot()
        stages = setup_stages(session, mode, mode_registry)
        active = _active_stage(session, mode, stages)
        guide_session = _state_session(session, mode, active)
        return SetupGuideSnapshot(
            guide_state(active, guide_session),
            mode.display_name if mode is not None else session.mode.value,
            active.stage_id,
            stages,
            available_actions(active, stages),
            status_message(active),
        )


def _session_required_snapshot() -> SetupGuideSnapshot:
    stage = SetupStageSnapshot(
        "open_session",
        "message",
        "Open or create a session",
        SetupStageStatus.ACTIVE,
        description="A session is required before setup can continue.",
        primary_action=SetupGuideAction("OpenSession", "Open Session"),
    )
    return SetupGuideSnapshot(
        SetupGuideState.SESSION_REQUIRED,
        "No active mode",
        stage.stage_id,
        (stage,),
        (stage.primary_action,) if stage.primary_action is not None else (),
        "No active session is loaded.",
    )


def _state_session(
    session: SessionRecord,
    mode: ModeDefinition | None,
    active: SetupStageSnapshot,
) -> SessionRecord:
    if mode is None or not mode.setup.stage_types:
        return session
    if active.status is SetupStageStatus.COMPLETE:
        return session
    return replace(session, setup=replace(session.setup, is_capture_ready=False))


def _active_stage(
    session: SessionRecord,
    mode: ModeDefinition | None,
    stages: tuple[SetupStageSnapshot, ...],
) -> SetupStageSnapshot:
    if _ready_after_required_setup(session, mode):
        return stages[-1]
    return active_stage(stages)


def _ready_after_required_setup(
    session: SessionRecord,
    mode: ModeDefinition | None,
) -> bool:
    if not session.setup.is_capture_ready:
        return False
    if mode is None:
        return True
    return not incomplete_required_setup_labels(session, mode)


__all__ = [
    "SetupGuideAction",
    "SetupGuideSnapshot",
    "SetupGuideState",
    "SetupGuideStateMachine",
    "SetupStageSnapshot",
    "SetupStageStatus",
]
