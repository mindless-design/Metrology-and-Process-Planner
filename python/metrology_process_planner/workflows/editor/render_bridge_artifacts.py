"""Artifact selection helpers for editor render refresh."""

from __future__ import annotations

from metrology_process_planner.domains.artifacts.artifact_query import first_display_artifact
from metrology_process_planner.domains.artifacts.artifact_visibility import (
    artifact_visible_for_session,
)
from metrology_process_planner.domains.session import ArtifactRecord, ModeRegistry, SessionRecord


def first_visible_display_artifact(
    session: SessionRecord,
    owner_type: str,
    owner_id: str,
    mode_registry: ModeRegistry | None = None,
) -> ArtifactRecord | None:
    """Return the preferred display artifact after applying mode visibility."""

    artifacts = {
        artifact_id: artifact
        for artifact_id, artifact in (session.artifacts or {}).items()
        if artifact_visible_for_session(session, artifact, mode_registry)
    }
    return first_display_artifact(artifacts, owner_type, owner_id)
