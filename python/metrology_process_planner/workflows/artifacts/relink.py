"""Artifact relink helpers."""

from __future__ import annotations

from dataclasses import replace

from metrology_process_planner.domains.session import (
    ArtifactPathMode,
    ArtifactRecord,
    ArtifactStatus,
    SessionRecord,
    WarningRecord,
)
from metrology_process_planner.persistence.paths import normalize_artifact_path
from metrology_process_planner.workflows.artifacts.warnings import (
    clear_open_warning,
    warning_id,
)


def relink_artifact_record(
    session: SessionRecord,
    artifact_id: str,
    relative_path: str,
) -> SessionRecord:
    """Update a managed artifact path and clear missing-warning state."""

    artifact = (session.artifacts or {}).get(artifact_id)
    if artifact is None:
        return session
    missing_warning = warning_id(artifact.id, "ARTIFACT_MISSING")
    warnings = _warnings_without_missing(session, missing_warning)
    artifacts = dict(session.artifacts or {})
    artifacts[artifact_id] = _relinked_artifact(artifact, relative_path, missing_warning)
    return replace(session, artifacts=artifacts, warnings=tuple(warnings.values()))


def _warnings_without_missing(
    session: SessionRecord,
    missing_warning: str,
) -> dict[str, WarningRecord]:
    warnings = {warning.id: warning for warning in session.warnings}
    clear_open_warning(warnings, missing_warning)
    return warnings


def _relinked_artifact(
    artifact: ArtifactRecord,
    relative_path: str,
    missing_warning: str,
) -> ArtifactRecord:
    return replace(
        artifact,
        relative_path=normalize_artifact_path(relative_path),
        path_mode=ArtifactPathMode.SESSION_RELATIVE,
        status=ArtifactStatus.PRESENT,
        warning_ids=tuple(item for item in artifact.warning_ids if item != missing_warning),
    )
