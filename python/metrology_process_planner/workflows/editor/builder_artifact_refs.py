"""Artifact reference view helpers for editor document building."""

from __future__ import annotations

from collections.abc import Mapping
from typing import Optional

from metrology_process_planner.domains.session import ArtifactRecord, SessionRecord
from metrology_process_planner.workflows.editor.references import ArtifactRef
from metrology_process_planner.workflows.editor.view_models import WarningViewModel


def _artifact_refs(
    artifacts: tuple[tuple[str, Optional[str]], ...],
    warning_artifacts: Mapping[str, WarningViewModel],
) -> tuple[ArtifactRef, ...]:
    return tuple(
        ArtifactRef(
            role=role,
            path=str(path),
            status=_artifact_status(str(path), warning_artifacts),
            message=warning_artifacts[str(path)].message
            if str(path) in warning_artifacts
            else "",
        )
        for role, path in artifacts
        if path
    )


def _artifact_refs_for_owner(
    session: SessionRecord,
    owner_type: str,
    owner_id: str,
) -> tuple[ArtifactRef, ...]:
    """Return editor artifact refs from the central artifact registry."""

    return tuple(
        _artifact_ref_from_record(artifact, *_warning_lookups(session))
        for artifact in (session.artifacts or {}).values()
        if artifact.owner.owner_type == owner_type and artifact.owner.owner_id == owner_id
    )


def _artifact_refs_by_id(
    session: SessionRecord,
    refs: Mapping[str, str],
    artifact_type: str = "",
) -> tuple[ArtifactRef, ...]:
    """Return editor artifact refs from explicit local artifact id refs."""

    artifacts = session.artifacts or {}
    return tuple(
        _artifact_ref_from_record(artifacts[artifact_id], *_warning_lookups(session))
        for artifact_id in refs.values()
        if artifact_id in artifacts
        and (not artifact_type or artifacts[artifact_id].type == artifact_type)
    )


def _artifact_ref_from_record(
    artifact: ArtifactRecord,
    warnings: Mapping[str, object],
    path_warnings: Mapping[str, object],
) -> ArtifactRef:
    message = ""
    status = _registry_status(artifact.status.value)
    for warning_id in artifact.warning_ids:
        warning = warnings.get(warning_id)
        if warning is not None:
            message = getattr(warning, "message", "")
            break
    path_warning = path_warnings.get(artifact.relative_path)
    if path_warning is not None:
        message = getattr(path_warning, "message", message)
        status = _warning_status(path_warning)
    return ArtifactRef(
        role=artifact.owner.role,
        path=artifact.relative_path,
        artifact_id=artifact.id,
        artifact_type=artifact.type,
        status=status,
        message=message,
        warning_ids=artifact.warning_ids,
        repair_action=artifact.repair.repair_action,
    )


def _warning_lookups(session: SessionRecord) -> tuple[dict[str, object], dict[str, object]]:
    return (
        {warning.id: warning for warning in session.warnings},
        {warning.artifact_path: warning for warning in session.warnings if warning.artifact_path},
    )


def _registry_status(status: str) -> str:
    if status == "present":
        return "available"
    if status == "failed":
        return "error"
    return status


def _warning_status(warning: object) -> str:
    message = str(getattr(warning, "message", "")).lower()
    if getattr(warning, "severity", "") == "error":
        return "error"
    if "stale" in message:
        return "stale"
    if "missing" in message:
        return "missing"
    return "missing"


def _artifact_status(
    path: str,
    warning_artifacts: Mapping[str, WarningViewModel],
) -> str:
    warning = warning_artifacts.get(path)
    if warning is None:
        return "available"
    message = warning.message.lower()
    if warning.severity == "error":
        return "error"
    if "stale" in message:
        return "stale"
    if "missing" in message:
        return "missing"
    return "missing"
