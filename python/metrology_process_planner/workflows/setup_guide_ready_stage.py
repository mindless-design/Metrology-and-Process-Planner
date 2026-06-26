"""Setup-guide readiness stage shared by recipe-free and process-aware modes."""

from __future__ import annotations

from metrology_process_planner.domains.session import ModeDefinition, SessionRecord
from metrology_process_planner.workflows.setup_guide_models import (
    SetupGuideAction,
    SetupStageSnapshot,
    SetupStageStatus,
)


def ready_stage(
    session: SessionRecord,
    mode: ModeDefinition | None = None,
) -> SetupStageSnapshot:
    """Return the final setup-readiness card."""

    missing = _missing_required(session, mode)
    complete = session.setup.is_capture_ready and not missing
    disabled_reason = _disabled_reason(complete, missing)
    return SetupStageSnapshot(
        "ready_for_capture",
        "ready_for_capture",
        "Ready for capture",
        SetupStageStatus.COMPLETE if complete else SetupStageStatus.BLOCKED,
        description="Setup can be marked ready after required stages are complete.",
        primary_action=SetupGuideAction(
            "MarkSetupComplete",
            "Mark Setup Complete",
            not disabled_reason,
            disabled_reason,
        ),
    )


def _disabled_reason(complete: bool, missing: tuple[str, ...]) -> str:
    if complete:
        return "Setup is already ready for capture."
    if missing:
        return "Complete required setup cards first: " + ", ".join(missing) + "."
    return ""


def _missing_required(session: SessionRecord, mode: ModeDefinition | None) -> tuple[str, ...]:
    if mode is None:
        return ()
    from metrology_process_planner.workflows.setup_guide_requirements import (
        incomplete_required_setup_labels,
    )

    return incomplete_required_setup_labels(session, mode)
