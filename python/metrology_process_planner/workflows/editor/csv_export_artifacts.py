"""Register capture CSV exports in the session artifact registry."""

from __future__ import annotations

import hashlib
from dataclasses import replace
from pathlib import Path

from metrology_process_planner.domains.session import (
    ArtifactDependencyRef,
    ArtifactFileMetadata,
    ArtifactOwnerRef,
    ArtifactRecord,
    ArtifactRepairMetadata,
    ArtifactStatus,
    ModeRegistry,
    SessionRecord,
    artifact_id,
)
from metrology_process_planner.persistence.paths import SessionPaths
from metrology_process_planner.workflows.artifacts.signatures import current_signature


def with_csv_export_artifact(
    session: SessionRecord,
    paths: SessionPaths,
    destination: Path,
    mode_registry: ModeRegistry | None = None,
) -> SessionRecord:
    """Return a session with the canonical capture CSV artifact upserted."""

    relative_path = _relative_path(destination, paths.folder)
    export_id = artifact_id("session", session.id, "csv_export")
    artifacts = {
        artifact_id_value: artifact
        for artifact_id_value, artifact in dict(session.artifacts or {}).items()
        if artifact_id_value != export_id
    }
    artifact = ArtifactRecord(
        id=export_id,
        type="csv_export",
        label="Capture CSV",
        relative_path=relative_path,
        owner=ArtifactOwnerRef("session", session.id, "csv_export"),
        status=ArtifactStatus.PRESENT,
        dependencies=(
            ArtifactDependencyRef(
                kind="session_data",
                id=session.id,
                signature=current_signature(session, "session_data", session.id, mode_registry),
            ),
        ),
        generator="csv_export",
        file=ArtifactFileMetadata(
            sha256=_sha256(destination),
            size_bytes=destination.stat().st_size if destination.exists() else None,
            content_type="text/csv",
        ),
        repair=ArtifactRepairMetadata(
            repair_action="rebuild_csv",
            repair_suggestion="Rebuild CSV from the current session data.",
            regenerable=True,
        ),
    )
    artifacts[artifact.id] = artifact
    return replace(session, artifacts=artifacts)


def _relative_path(path: Path, session_folder: Path) -> str:
    try:
        return path.resolve().relative_to(session_folder.resolve()).as_posix()
    except ValueError:
        return path.as_posix()


def _sha256(path: Path) -> str | None:
    if not path.exists():
        return None
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return "sha256:" + digest.hexdigest()
