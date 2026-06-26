"""State-machine summary rows for Advanced Diagnostics."""

from __future__ import annotations

from collections.abc import Mapping

from metrology_process_planner.domains.artifacts.artifact_visibility import (
    artifact_visible_for_session,
)
from metrology_process_planner.domains.session import ModeRegistry, SessionRecord
from metrology_process_planner.workflows.setup_guide_models import SetupStageStatus
from metrology_process_planner.workflows.setup_guide_requirements import (
    incomplete_required_setup_labels,
)
from metrology_process_planner.workflows.setup_guide_stages import setup_stages
from metrology_process_planner.workflows.ui_state_machines import (
    ArtifactRepairStateMachine,
    MeasurementWorkflowStateMachine,
    RecipeContextStateMachine,
    SessionUIStateMachine,
)


def workflow_state_rows(
    session: SessionRecord,
    mode_registry: ModeRegistry | None = None,
) -> tuple[tuple[str, str], ...]:
    """Return durable workflow state rows for the diagnostics summary."""

    return (
        ("Workflow State", SessionUIStateMachine().evaluate(session).state),
        ("Setup State", _setup_state(session, mode_registry)),
        ("Capture State", _capture_state(session)),
        ("Measurement Workflow", MeasurementWorkflowStateMachine().evaluate(session).state),
        *_grid_state_rows(session, mode_registry),
        ("Armed Capture Tool", session.workflow.active_primitive or "none"),
        ("Recipe Context", RecipeContextStateMachine(mode_registry).evaluate(session).state),
        ("Artifact Repair", ArtifactRepairStateMachine(mode_registry).evaluate(session).state),
    )


def _setup_state(session: SessionRecord, mode_registry: ModeRegistry | None) -> str:
    if mode_registry is not None:
        mode = mode_registry.definition(session.mode.value)
        if mode.setup.stage_types:
            return _mode_setup_state(session, mode_registry)
    if session.setup.is_capture_ready:
        return "ready"
    if session.setup.items:
        complete = sum(1 for item in session.setup.items if item.status == "complete")
        return f"incomplete ({complete}/{len(session.setup.items)} complete)"
    return "not_required"


def _mode_setup_state(session: SessionRecord, mode_registry: ModeRegistry) -> str:
    mode = mode_registry.definition(session.mode.value)
    stages = setup_stages(session, mode, mode_registry)
    missing_required = incomplete_required_setup_labels(session, mode)
    if session.setup.is_capture_ready and not missing_required:
        return "ready"
    complete = sum(
        1
        for stage in stages
        if stage.status in (SetupStageStatus.COMPLETE, SetupStageStatus.SKIPPED)
    )
    return f"incomplete ({complete}/{len(stages)} complete)"


def _capture_state(session: SessionRecord) -> str:
    if session.pending_captures:
        return "pending_review"
    if session.workflow.active and session.workflow.active_primitive:
        return f"armed_{session.workflow.active_primitive}"
    if session.captures:
        return "saved"
    return "idle"


def _grid_state_rows(
    session: SessionRecord,
    mode_registry: ModeRegistry | None,
) -> tuple[tuple[str, str], ...]:
    if not session.grid_datasets:
        return (
            ("Grid Datasets", "0"),
            ("Grid Planned Sites", "0"),
            ("Grid Overview Artifacts", "none"),
        )
    return (
        ("Grid Datasets", str(len(session.grid_datasets))),
        ("Grid Planned Sites", str(_planned_site_count(session))),
        ("Grid Overview Artifacts", _grid_overview_statuses(session, mode_registry)),
    )


def _planned_site_count(session: SessionRecord) -> int:
    return sum(
        _metadata_int(dataset.metadata, "planned_site_count")
        for dataset in session.grid_datasets
    )


def _grid_overview_statuses(
    session: SessionRecord,
    mode_registry: ModeRegistry | None,
) -> str:
    counts: dict[str, int] = {}
    for dataset in session.grid_datasets:
        artifact_id = str(dict(dataset.artifact_refs or {}).get("grid_overview", ""))
        artifact = (session.artifacts or {}).get(artifact_id) if artifact_id else None
        status = (
            artifact.status.value
            if artifact is not None
            and artifact_visible_for_session(session, artifact, mode_registry)
            else "missing"
        )
        counts[status] = counts.get(status, 0) + 1
    return ", ".join(f"{status}:{counts[status]}" for status in sorted(counts))


def _metadata_int(metadata: object, key: str) -> int:
    if not isinstance(metadata, Mapping):
        return 0
    try:
        return int(metadata.get(key, 0))
    except (TypeError, ValueError):
        return 0
