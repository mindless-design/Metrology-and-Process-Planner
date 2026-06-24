"""Explicit setup-guide workflow state machine."""

from __future__ import annotations

from metrology_process_planner.domains.session import ModeDefinition, SessionRecord
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
from metrology_process_planner.workflows.setup_guide_stages import setup_stages


class SetupGuideStateMachine:
    """Resolve setup-guide state from canonical session and mode policy."""

    def evaluate(
        self,
        session: SessionRecord | None,
        mode: ModeDefinition | None = None,
    ) -> SetupGuideSnapshot:
        """Return a deterministic setup-guide snapshot."""

        if session is None:
            return _session_required_snapshot()
        stages = setup_stages(session, mode)
        active = active_stage(stages)
        return SetupGuideSnapshot(
            guide_state(active, session),
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


__all__ = [
    "SetupGuideAction",
    "SetupGuideSnapshot",
    "SetupGuideState",
    "SetupGuideStateMachine",
    "SetupStageSnapshot",
    "SetupStageStatus",
]
