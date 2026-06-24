"""State-machine summary rows for Advanced Diagnostics."""

from __future__ import annotations

from metrology_process_planner.domains.session import SessionRecord
from metrology_process_planner.workflows.ui_state_machines import (
    ArtifactRepairStateMachine,
    RecipeContextStateMachine,
    SessionUIStateMachine,
)


def workflow_state_rows(session: SessionRecord) -> tuple[tuple[str, str], ...]:
    """Return durable workflow state rows for the diagnostics summary."""

    return (
        ("Workflow State", SessionUIStateMachine().evaluate(session).state),
        ("Armed Capture Tool", session.workflow.active_primitive or "none"),
        ("Recipe Context", RecipeContextStateMachine().evaluate(session).state),
        ("Artifact Repair", ArtifactRepairStateMachine().evaluate(session).state),
    )
