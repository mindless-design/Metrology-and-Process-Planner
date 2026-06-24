"""Presenter for the modeless setup guide."""

from __future__ import annotations

from metrology_process_planner.domains.session import (
    ModeRegistry,
    SessionRecord,
    built_in_mode_registry,
)
from metrology_process_planner.ui.capture.status import capture_status_text
from metrology_process_planner.ui.shell import SetupGuideViewModel, SetupStageViewModel
from metrology_process_planner.workflows.setup_guide_state import (
    SetupGuideAction,
    SetupGuideSnapshot,
    SetupGuideStateMachine,
    SetupStageSnapshot,
)


class SetupGuidePresenter:
    """Build setup guide view models from canonical session state."""

    def __init__(
        self,
        state_machine: SetupGuideStateMachine | None = None,
        mode_registry: ModeRegistry | None = None,
    ) -> None:
        self._state_machine = state_machine or SetupGuideStateMachine()
        self._mode_registry = mode_registry or built_in_mode_registry()

    def build(self, session: SessionRecord | None) -> SetupGuideViewModel:
        """Return the current setup guide view model."""

        mode = self._mode_registry.definition(session.mode.value) if session is not None else None
        snapshot = self._state_machine.evaluate(session, mode)
        active = _active_snapshot_stage(snapshot)
        return SetupGuideViewModel(
            session.name if session is not None else "No active session",
            snapshot.active_stage_id,
            tuple(_stage_view(stage) for stage in snapshot.stages),
            tuple(action.command_id for action in snapshot.actions),
            snapshot.state.value,
            snapshot.mode_display_name,
            active.label,
            _next_action_label(snapshot.actions),
            _warning_count(snapshot),
            capture_status_text(session) if session is not None else "",
        )


def _stage_view(stage: SetupStageSnapshot) -> SetupStageViewModel:
    primary = stage.primary_action.command_id if stage.primary_action is not None else ""
    return SetupStageViewModel(
        stage.stage_id,
        stage.label,
        stage.status.value,
        stage.primary_action.label if stage.primary_action is not None else "",
        stage.stage_type,
        stage.required,
        stage.description,
        primary,
        tuple(action.command_id for action in stage.secondary_actions),
        _disabled_reason(stage.primary_action),
        len(stage.warning_ids),
    )


def _active_snapshot_stage(snapshot: SetupGuideSnapshot) -> SetupStageSnapshot:
    for stage in snapshot.stages:
        if stage.stage_id == snapshot.active_stage_id:
            return stage
    return snapshot.stages[0]


def _next_action_label(actions: tuple[SetupGuideAction, ...]) -> str:
    for action in actions:
        if action.enabled:
            return action.label
    return ""


def _disabled_reason(action: SetupGuideAction | None) -> str:
    if action is None or action.enabled:
        return ""
    return action.disabled_reason


def _warning_count(snapshot: SetupGuideSnapshot) -> int:
    return sum(len(stage.warning_ids) for stage in snapshot.stages)
