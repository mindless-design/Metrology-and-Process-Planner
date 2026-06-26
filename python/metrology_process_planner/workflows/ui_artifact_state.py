"""Artifact repair state helpers for modeless UI summaries."""

from __future__ import annotations

from metrology_process_planner.domains.session import (
    ArtifactRecord,
    ArtifactStatus,
    ModeRegistry,
    SessionRecord,
)
from metrology_process_planner.workflows.artifacts.repair_support import (
    is_process_only_repair_artifact,
)
from metrology_process_planner.workflows.editor.builder_basics import mode_is_process_aware
from metrology_process_planner.workflows.ui_state_models import UiStateSnapshot


def artifact_repair_snapshot(
    session: SessionRecord,
    mode_registry: ModeRegistry | None = None,
) -> UiStateSnapshot:
    """Return artifact repair state for diagnostics and editor warnings."""

    repairable = _repairable_artifacts(session, mode_registry)
    if not repairable:
        return UiStateSnapshot("artifact_repair", "idle", "No artifact repair tasks.")
    return _artifact_repair_state(session, repairable, mode_registry)


def _repairable_artifacts(
    session: SessionRecord,
    mode_registry: ModeRegistry | None,
) -> tuple[ArtifactRecord, ...]:
    repairable_statuses = {
        ArtifactStatus.MISSING,
        ArtifactStatus.STALE,
        ArtifactStatus.FAILED,
        ArtifactStatus.PENDING,
        ArtifactStatus.PENDING_SOLVER,
        ArtifactStatus.PLACEHOLDER,
    }
    return tuple(
        artifact
        for artifact in (session.artifacts or {}).values()
        if (
            artifact.status in repairable_statuses
            and not is_process_only_repair_artifact(session, artifact, mode_registry)
            and (
                artifact.status is not ArtifactStatus.PLACEHOLDER
                or bool(artifact.repair.repair_action or artifact.repair.regenerable)
            )
        )
    )


def _artifact_repair_state(
    session: SessionRecord,
    repairable: tuple[ArtifactRecord, ...],
    mode_registry: ModeRegistry | None,
) -> UiStateSnapshot:
    warning_ids = tuple(
        dict.fromkeys(item for artifact in repairable for item in artifact.warning_ids)
    )
    return UiStateSnapshot(
        "artifact_repair",
        "open_tasks",
        f"{len(repairable)} artifact repair task(s).",
        repairable[0].id,
        _repair_actions(session, mode_registry),
        warning_ids,
    )


def _repair_actions(
    session: SessionRecord,
    mode_registry: ModeRegistry | None,
) -> tuple[str, ...]:
    actions = ["RegenerateArtifact"]
    if mode_is_process_aware(session, mode_registry):
        actions.append("RegenerateProcessOutput")
    return tuple(actions)
