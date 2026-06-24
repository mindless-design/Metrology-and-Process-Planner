"""Presenter for the modeless setup guide."""

from __future__ import annotations

from metrology_process_planner.domains.session import SessionRecord
from metrology_process_planner.ui.shell import SetupGuideViewModel, SetupStageViewModel


class SetupGuidePresenter:
    """Build setup guide view models from canonical session state."""

    def build(self, session: SessionRecord | None) -> SetupGuideViewModel:
        """Return the current setup guide view model."""

        if session is None:
            return SetupGuideViewModel(
                "No active session",
                "open_session",
                (_stage("open_session", "Open or create a session", "active"),),
                ("OpenSession",),
                "unavailable",
            )
        setup = session.setup
        stages = (
            _stage("coordinates", "Choose coordinate frame", _status(bool(setup.coordinate_mode))),
            _stage("origin", "Capture or accept origin", _status(setup.origin is not None)),
            _stage("alignment", "Capture alignment marks", _status(bool(setup.alignments))),
            _stage("complete", "Mark setup complete", _status(setup.is_capture_ready)),
        )
        return SetupGuideViewModel(
            session.name,
            _active_stage(stages),
            stages,
            (
                "UseGlobalCoordinates",
                "StartOriginCapture",
                "CaptureAlignmentMark",
                "MarkSetupComplete",
            ),
        )


def _stage(stage_id: str, label: str, status: str) -> SetupStageViewModel:
    return SetupStageViewModel(stage_id, label, status, _next_action(status, label))


def _status(done: bool) -> str:
    return "complete" if done else "pending"


def _next_action(status: str, label: str) -> str:
    return "" if status == "complete" else label


def _active_stage(stages: tuple[SetupStageViewModel, ...]) -> str:
    for stage in stages:
        if stage.status != "complete":
            return stage.stage_id
    return stages[-1].stage_id
