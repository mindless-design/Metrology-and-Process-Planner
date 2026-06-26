"""Artifact scan summary helpers."""

from __future__ import annotations

from pathlib import Path

from metrology_process_planner.domains.artifacts.artifact_visibility import (
    artifact_visible_for_session,
)
from metrology_process_planner.domains.session import (
    ArtifactRecord,
    ArtifactStatus,
    ModeRegistry,
    SessionRecord,
    utc_now_iso,
)
from metrology_process_planner.persistence.paths import SessionPaths
from metrology_process_planner.workflows.artifacts.scan_result import ArtifactScanResult


def scan_result(
    session: SessionRecord,
    mode_registry: ModeRegistry | None = None,
) -> ArtifactScanResult:
    """Return a compact artifact scan result for the updated session."""

    checked_at = utc_now_iso()
    artifacts = tuple(
        artifact
        for artifact in (session.artifacts or {}).values()
        if artifact_visible_for_session(session, artifact, mode_registry)
    )
    artifact_ids = {artifact.id for artifact in artifacts}
    statuses = tuple((artifact.id, artifact.status) for artifact in artifacts)
    warning_ids = tuple(
        warning.id
        for warning in session.warnings
        if warning.source == "artifact"
        and _warning_visible_for_artifacts(warning.related_artifact_refs, artifact_ids)
    )
    return ArtifactScanResult.from_statuses(
        session.id,
        checked_at,
        statuses,
        warning_ids,
        _repair_candidates(artifacts),
    )


def paths_from(paths: SessionPaths | Path | str) -> SessionPaths:
    """Normalize user-provided scanner paths."""

    if isinstance(paths, SessionPaths):
        return paths
    return SessionPaths.for_folder(Path(paths))


def _repair_candidates(artifacts: tuple[ArtifactRecord, ...]) -> tuple[str, ...]:
    repairable_statuses = {
        ArtifactStatus.MISSING,
        ArtifactStatus.STALE,
        ArtifactStatus.FAILED,
    }
    return tuple(
        artifact.id
        for artifact in artifacts
        if artifact.repair.regenerable and artifact.status in repairable_statuses
    )


def _warning_visible_for_artifacts(
    related_artifact_refs: tuple[str, ...],
    artifact_ids: set[str],
) -> bool:
    return not related_artifact_refs or bool(artifact_ids.intersection(related_artifact_refs))
