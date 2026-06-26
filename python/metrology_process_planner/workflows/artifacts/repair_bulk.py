"""Bulk artifact repair helpers."""

from __future__ import annotations

from collections.abc import Callable

from metrology_process_planner.domains.session import ArtifactStatus, ModeRegistry, SessionRecord
from metrology_process_planner.persistence.paths import SessionPaths
from metrology_process_planner.workflows.artifacts.repair_support import (
    is_process_only_repair_artifact,
)


def repair_all_with_status(
    session: SessionRecord,
    paths: SessionPaths,
    status: ArtifactStatus,
    repair_one: Callable[
        [SessionRecord, str, SessionPaths, ModeRegistry | None],
        SessionRecord,
    ],
    mode_registry: ModeRegistry | None = None,
) -> SessionRecord:
    """Repair all artifacts with one lifecycle status."""

    current = session
    for artifact in tuple((current.artifacts or {}).values()):
        if artifact.status is status and not is_process_only_repair_artifact(
            current,
            artifact,
            mode_registry,
        ):
            current = repair_one(current, artifact.id, paths, mode_registry)
    return current
