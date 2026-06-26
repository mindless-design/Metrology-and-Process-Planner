"""Setup-guide status derived from the active canvas workflow."""

from __future__ import annotations

from dataclasses import replace

from metrology_process_planner.domains.session import SessionRecord
from metrology_process_planner.workflows.setup_guide_models import (
    SetupStageSnapshot,
    SetupStageStatus,
)


def workflow_stage_status(
    session: SessionRecord,
    stage_type: str,
    fallback: SetupStageStatus,
) -> SetupStageStatus:
    """Return live setup-capture status when the canvas is armed for this stage."""

    if _workflow_matches_stage(session, stage_type):
        return SetupStageStatus.WAITING_FOR_CANVAS_CAPTURE
    return fallback


def overlay_workflow_status(
    stage: SetupStageSnapshot,
    session: SessionRecord,
) -> SetupStageSnapshot:
    """Prefer live canvas workflow state over persisted setup item status."""

    status = workflow_stage_status(session, stage.stage_type, stage.status)
    if status is stage.status:
        return stage
    return replace(stage, status=status)


def _workflow_matches_stage(session: SessionRecord, stage_type: str) -> bool:
    workflow = session.workflow
    if not workflow.active:
        return False
    return workflow.stage == stage_type or workflow.pending_item_ref == f"setup:{stage_type}"
