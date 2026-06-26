"""Mode-aware visibility helpers for report models."""

from __future__ import annotations

from metrology_process_planner.domains.artifacts.artifact_visibility import (
    artifact_visible_for_session,
)
from metrology_process_planner.domains.session import ModeRegistry, SessionRecord


def visible_artifact_refs(
    session: SessionRecord,
    artifact_ids: tuple[str, ...],
    mode_registry: ModeRegistry | None = None,
) -> tuple[str, ...]:
    """Return artifact refs that should appear in normal report summaries."""

    artifacts = session.artifacts or {}
    return tuple(
        artifact_id
        for artifact_id in artifact_ids
        if artifact_id in artifacts
        and artifact_visible_for_session(session, artifacts[artifact_id], mode_registry)
    )
