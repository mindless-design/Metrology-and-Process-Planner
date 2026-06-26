"""Setup-guide artifact badge helpers."""

from __future__ import annotations

from collections.abc import Mapping

from metrology_process_planner.domains.artifacts.artifact_visibility import (
    artifact_visible_for_session,
)
from metrology_process_planner.domains.modes.mode_registry import ModeRegistry
from metrology_process_planner.domains.session import ArtifactRecord, SessionRecord


def artifact_badge(
    artifact_refs: Mapping[str, str] | None,
    artifacts: Mapping[str, ArtifactRecord] | None,
    session: SessionRecord | None = None,
    mode_registry: ModeRegistry | None = None,
) -> str:
    """Return a compact setup-card artifact availability badge."""

    refs = tuple(_visible_refs(artifact_refs, artifacts, session, mode_registry))
    if not refs:
        return "none"
    statuses = tuple(_status(artifact_id, artifacts) for artifact_id in refs)
    unique = set(statuses)
    if len(unique) == 1:
        return statuses[0]
    return _highest_priority_status(unique)


def _highest_priority_status(statuses: set[str]) -> str:
    for status in ("failed", "missing", "stale"):
        if status in statuses:
            return status
    return "mixed"


def _status(
    artifact_id: str,
    artifacts: Mapping[str, ArtifactRecord] | None,
) -> str:
    artifact = (artifacts or {}).get(artifact_id)
    if artifact is None:
        return "missing"
    return artifact.status.value


def _visible_refs(
    artifact_refs: Mapping[str, str] | None,
    artifacts: Mapping[str, ArtifactRecord] | None,
    session: SessionRecord | None,
    mode_registry: ModeRegistry | None,
) -> tuple[str, ...]:
    refs = tuple((artifact_refs or {}).values())
    if session is None:
        return refs
    registry = artifacts or {}
    return tuple(
        artifact_id
        for artifact_id in refs
        if artifact_id not in registry
        or artifact_visible_for_session(session, registry[artifact_id], mode_registry)
    )
