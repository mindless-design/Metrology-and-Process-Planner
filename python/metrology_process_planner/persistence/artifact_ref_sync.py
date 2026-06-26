"""Mode-aware artifact reference synchronization helpers."""

from __future__ import annotations

from metrology_process_planner.domains.artifacts.artifact_visibility import (
    artifact_visible_for_session,
)
from metrology_process_planner.domains.session import ArtifactRecord, ModeRegistry, SessionRecord


def visible_artifact_refs_for_owner(
    session: SessionRecord,
    artifacts: dict[str, ArtifactRecord],
    owner_type: str,
    owner_id: str,
    mode_registry: ModeRegistry | None = None,
) -> dict[str, str]:
    """Return owner refs that belong in normal mode-scoped records."""

    return {
        artifact.owner.role: artifact.id
        for artifact in artifacts.values()
        if artifact.owner.owner_type == owner_type
        and artifact.owner.owner_id == owner_id
        and artifact_visible_for_session(session, artifact, mode_registry)
    }
