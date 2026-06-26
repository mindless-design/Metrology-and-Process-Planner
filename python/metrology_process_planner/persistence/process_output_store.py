"""Persistence for generated process-output artifacts."""

from __future__ import annotations

import hashlib
import json
from dataclasses import replace
from pathlib import Path

from metrology_process_planner.domains.session import (
    ArtifactFileMetadata,
    ArtifactRecord,
    ArtifactRepairMetadata,
    ArtifactStatus,
    ProcessOutputRecord,
    SessionRecord,
)
from metrology_process_planner.persistence.paths import SessionPaths, artifact_path_to_disk


class ProcessOutputStore:
    """Write ready process-output records as session-relative JSON artifacts."""

    def export_ready_outputs(
        self,
        paths: SessionPaths,
        session: SessionRecord,
        owner_id: str = "",
    ) -> SessionRecord:
        """Persist ready outputs and return a session with present artifact records."""

        paths.ensure_created()
        artifacts = dict(session.artifacts or {})
        outputs = []
        for output in session.process_outputs:
            if not _should_export(output, owner_id):
                outputs.append(output)
                continue
            output, artifacts = _export_output(paths, output, artifacts)
            outputs.append(output)
        return replace(session, process_outputs=tuple(outputs), artifacts=artifacts)


def _should_export(output: ProcessOutputRecord, owner_id: str) -> bool:
    if output.status != "ready":
        return False
    if not owner_id:
        return True
    return str(dict(output.metadata or {}).get("capture_id", "")) == owner_id


def _export_output(
    paths: SessionPaths,
    output: ProcessOutputRecord,
    artifacts: dict[str, ArtifactRecord],
) -> tuple[ProcessOutputRecord, dict[str, ArtifactRecord]]:
    exported_refs: dict[str, str] = {}
    for role, artifact_id in dict(output.artifact_refs or {}).items():
        artifact = artifacts.get(artifact_id)
        if artifact is None or artifact.type != "process_output":
            continue
        payload = _payload(output, role)
        disk_path = artifact_path_to_disk(paths.folder, artifact.relative_path)
        metadata = _write_json(disk_path, payload)
        artifacts[artifact.id] = _present_artifact(artifact, metadata)
        exported_refs[role] = artifact.id
    if not exported_refs:
        return output, artifacts
    return (
        replace(output, artifact_refs={**dict(output.artifact_refs or {}), **exported_refs}),
        artifacts,
    )


def _payload(output: ProcessOutputRecord, role: str) -> dict[str, object]:
    return {
        "role": role,
        "process_output": output.to_dict(),
    }


def _write_json(path: Path, payload: dict[str, object]) -> ArtifactFileMetadata:
    path.parent.mkdir(parents=True, exist_ok=True)
    data = json.dumps(payload, indent=2).encode("utf-8") + b"\n"
    path.write_bytes(data)
    return ArtifactFileMetadata(
        sha256=hashlib.sha256(data).hexdigest(),
        size_bytes=path.stat().st_size,
        content_type="application/json",
    )


def _present_artifact(
    artifact: ArtifactRecord,
    file_metadata: ArtifactFileMetadata,
) -> ArtifactRecord:
    return replace(
        artifact,
        status=ArtifactStatus.PRESENT,
        generator="ProcessOutputStore",
        file=file_metadata,
        repair=ArtifactRepairMetadata(
            "regenerate_process_output",
            "Regenerate process output.",
            regenerable=True,
            requires_recipe=True,
            requires_solver=True,
        ),
        warning_ids=(),
    )
