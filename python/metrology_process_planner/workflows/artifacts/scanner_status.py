"""Status update helpers for artifact scanner records."""

from __future__ import annotations

from dataclasses import replace

from metrology_process_planner.domains.session import (
    ArtifactDependencyRef,
    ArtifactRecord,
    ArtifactStatus,
    ModeRegistry,
    SessionRecord,
    WarningRecord,
)
from metrology_process_planner.persistence.paths import SessionPaths, artifact_path_to_disk
from metrology_process_planner.workflows.artifacts.signatures import current_signature
from metrology_process_planner.workflows.artifacts.warnings import (
    ARTIFACT_FAILED,
    ARTIFACT_MISSING,
    ARTIFACT_STALE,
    artifact_warning,
    clear_open_warning,
    upsert_warning,
    warning_id,
)


def with_file_status(
    artifact: ArtifactRecord,
    paths: SessionPaths,
    warnings: dict[str, WarningRecord],
) -> ArtifactRecord:
    """Return one artifact with file-existence status refreshed."""

    if _is_external(artifact):
        return replace(artifact, status=ArtifactStatus.EXTERNAL)
    if _preserves_file_status(artifact):
        return artifact
    warning_id_value = warning_id(artifact.id, ARTIFACT_MISSING)
    exists, details = _exists(paths, artifact)
    if exists:
        clear_open_warning(warnings, warning_id_value)
        return without_warning(artifact, warning_id_value, ArtifactStatus.PRESENT)
    return _missing_artifact_status(artifact, details, warnings)


def _missing_artifact_status(
    artifact: ArtifactRecord,
    details: str,
    warnings: dict[str, WarningRecord],
) -> ArtifactRecord:
    warning = artifact_warning(
        artifact,
        ARTIFACT_MISSING,
        f"Missing artifact: {artifact.label or artifact.id}",
        details or f"Artifact file is missing: {artifact.relative_path}",
        "Regenerate or relink the artifact from the session editor.",
    )
    return with_warning(replace(artifact, status=ArtifactStatus.MISSING), warning, warnings)


def with_stale_status(
    session: SessionRecord,
    artifact: ArtifactRecord,
    warnings: dict[str, WarningRecord],
    mode_registry: ModeRegistry | None,
) -> ArtifactRecord:
    """Return one artifact with dependency staleness status refreshed."""

    if artifact.status is not ArtifactStatus.PRESENT:
        return artifact
    if not _is_stale(session, artifact, mode_registry):
        clear_open_warning(warnings, warning_id(artifact.id, ARTIFACT_STALE))
        return without_warning(artifact, warning_id(artifact.id, ARTIFACT_STALE))
    warning = artifact_warning(
        artifact,
        _stale_code(artifact),
        f"Stale artifact: {artifact.label or artifact.id}",
        "One or more dependency signatures changed since generation.",
        _stale_suggestion(artifact),
    )
    return with_warning(replace(artifact, status=ArtifactStatus.STALE), warning, warnings)


def failure_warning(artifact: ArtifactRecord) -> WarningRecord:
    """Return the warning used for a failed artifact generation."""

    return artifact_warning(
        artifact,
        ARTIFACT_FAILED,
        f"Artifact generation failed: {artifact.label or artifact.id}",
        artifact.repair.last_error or "The last generator attempt did not complete.",
        artifact.repair.repair_suggestion or "Retry generation from the session editor.",
        severity="error",
    )


def with_warning(
    artifact: ArtifactRecord,
    warning: WarningRecord,
    warnings: dict[str, WarningRecord],
) -> ArtifactRecord:
    """Attach or update one warning on an artifact record."""

    stored = upsert_warning(warnings, warning)
    ids = tuple(sorted(set(artifact.warning_ids + (stored.id,))))
    return replace(artifact, warning_ids=ids)


def without_warning(
    artifact: ArtifactRecord,
    warning_id_value: str,
    status: ArtifactStatus | None = None,
) -> ArtifactRecord:
    """Remove one warning reference from an artifact record."""

    new_status = artifact.status if status is None else status
    ids = tuple(item for item in artifact.warning_ids if item != warning_id_value)
    return replace(artifact, status=new_status, warning_ids=ids)


def _is_stale(
    session: SessionRecord,
    artifact: ArtifactRecord,
    mode_registry: ModeRegistry | None,
) -> bool:
    if any(
        _dependency_changed(session, dependency, mode_registry)
        for dependency in artifact.dependencies
    ):
        return True
    current = _dependency_signature(session, artifact, mode_registry)
    return bool(artifact.dependency_signature and current != artifact.dependency_signature)


def _preserves_file_status(artifact: ArtifactRecord) -> bool:
    return artifact.status in {
        ArtifactStatus.STALE,
        ArtifactStatus.PENDING,
        ArtifactStatus.PENDING_SOLVER,
        ArtifactStatus.FAILED,
        ArtifactStatus.PLACEHOLDER,
    }


def _dependency_changed(
    session: SessionRecord,
    dependency: ArtifactDependencyRef,
    mode_registry: ModeRegistry | None,
) -> bool:
    if not dependency.signature or not dependency.kind:
        return False
    current = current_signature(session, dependency.kind, dependency.id, mode_registry)
    return bool(current and current != dependency.signature)


def _dependency_signature(
    session: SessionRecord,
    artifact: ArtifactRecord,
    mode_registry: ModeRegistry | None,
) -> str:
    parts = []
    for dependency in artifact.dependencies:
        if dependency.kind and dependency.id:
            parts.append(current_signature(session, dependency.kind, dependency.id, mode_registry))
    return "|".join(parts)


def _stale_code(artifact: ArtifactRecord) -> str:
    if artifact.type == "csv_export":
        return "CSV_STALE"
    if artifact.type in _REPORT_ARTIFACT_TYPES:
        return "REPORT_STALE"
    return ARTIFACT_STALE


def _stale_suggestion(artifact: ArtifactRecord) -> str:
    if artifact.type == "csv_export":
        return "Rebuild CSV from the current session data."
    if artifact.type in _REPORT_ARTIFACT_TYPES:
        return "Rebuild the report from current artifacts."
    return "Regenerate the artifact from the session editor."


def _is_external(artifact: ArtifactRecord) -> bool:
    return artifact.path_mode.value == "external" or artifact.status is ArtifactStatus.EXTERNAL


def _exists(paths: SessionPaths, artifact: ArtifactRecord) -> tuple[bool, str]:
    try:
        return artifact_path_to_disk(paths.folder, artifact.relative_path).exists(), ""
    except ValueError as exc:
        return False, str(exc)


_REPORT_ARTIFACT_TYPES = {
    "powerpoint_deck",
    "powerpoint_export",
    "pdf_report",
    "image_bundle",
    "report",
    "report_manifest",
}
