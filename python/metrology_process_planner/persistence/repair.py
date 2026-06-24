"""Repair-oriented validation for session artifacts."""

from __future__ import annotations

from dataclasses import dataclass, replace

from metrology_process_planner.domains.session import (
    ArtifactRecord,
    ArtifactStatus,
    SessionRecord,
    WarningRecord,
)
from metrology_process_planner.persistence.paths import SessionPaths, artifact_path_to_disk


def validate_artifact_files(session: SessionRecord, paths: SessionPaths) -> SessionRecord:
    """Return a session whose artifact statuses reflect files on disk."""

    artifacts: dict[str, ArtifactRecord] = {}
    warnings = {warning.id: warning for warning in session.warnings}
    for artifact_id, artifact in (session.artifacts or {}).items():
        checked = _validate_artifact_file(artifact_id, artifact, paths, warnings)
        artifacts[artifact_id] = checked.artifact
    return replace(session, artifacts=artifacts, warnings=tuple(warnings.values()))


@dataclass(frozen=True)
class _CheckedArtifact:
    artifact: ArtifactRecord


def _validate_artifact_file(
    artifact_id: str,
    artifact: ArtifactRecord,
    paths: SessionPaths,
    warnings: dict[str, WarningRecord],
) -> _CheckedArtifact:
    if _is_external(artifact):
        return _CheckedArtifact(artifact)
    warning_id = _missing_warning_id(artifact_id)
    exists, details = _artifact_file_exists(paths, artifact)
    if exists:
        _clear_missing_warning(warnings, warning_id)
        return _CheckedArtifact(_without_warning(artifact, warning_id))
    warning = warnings.get(warning_id) or _warning(
        artifact,
        warning_id,
        details or f"Artifact file is missing: {artifact.relative_path}",
    )
    warnings[warning_id] = warning
    return _CheckedArtifact(_with_missing_warning(artifact, warning_id))


def _is_external(artifact: ArtifactRecord) -> bool:
    return artifact.path_mode.value == "external" or artifact.status is ArtifactStatus.EXTERNAL


def _artifact_file_exists(paths: SessionPaths, artifact: ArtifactRecord) -> tuple[bool, str]:
    try:
        return artifact_path_to_disk(paths.folder, artifact.relative_path).exists(), ""
    except ValueError as exc:
        return False, str(exc)


def _clear_missing_warning(warnings: dict[str, WarningRecord], warning_id: str) -> None:
    if warning_id in warnings and warnings[warning_id].code == "artifact_missing":
        warnings.pop(warning_id)


def _with_missing_warning(artifact: ArtifactRecord, warning_id: str) -> ArtifactRecord:
    return replace(
        artifact,
        status=ArtifactStatus.MISSING,
        warning_ids=tuple(sorted(set(artifact.warning_ids + (warning_id,)))),
    )


def _without_warning(artifact: ArtifactRecord, warning_id: str) -> ArtifactRecord:
    return replace(
        artifact,
        warning_ids=tuple(item for item in artifact.warning_ids if item != warning_id),
    )


def _warning(
    artifact: ArtifactRecord,
    warning_id: str,
    details: str,
) -> WarningRecord:
    return WarningRecord(
        id=warning_id,
        message=f"Missing artifact: {artifact.label or artifact.id}",
        severity="warning",
        artifact_path=artifact.relative_path,
        source="artifact_repair",
        code="artifact_missing",
        related_artifact_refs=(artifact.id,),
        technical_details=details,
        repair_suggestion="Regenerate the artifact from the session editor.",
    )


def _missing_warning_id(artifact_id: str) -> str:
    return f"artifact-{artifact_id}-missing"
