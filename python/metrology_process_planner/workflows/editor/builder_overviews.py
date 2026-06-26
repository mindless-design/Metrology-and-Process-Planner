"""Overview item discovery helpers for editor document building."""

from __future__ import annotations

from metrology_process_planner.domains.artifacts.artifact_visibility import (
    artifact_visible_for_session,
)
from metrology_process_planner.domains.session import ModeRegistry, SessionRecord


def overview_roles(
    session: SessionRecord,
    mode_registry: ModeRegistry | None = None,
) -> tuple[str, ...]:
    """Return visible overview artifact roles for the active mode."""

    roles = {
        artifact.owner.role
        for artifact in (session.artifacts or {}).values()
        if artifact_visible_for_session(session, artifact, mode_registry)
        and _is_overview_artifact(artifact.type)
    }
    return tuple(sorted(roles))


def _is_overview_artifact(artifact_type: str) -> bool:
    return artifact_type.endswith("_overview_image") or artifact_type == "overview_image"
