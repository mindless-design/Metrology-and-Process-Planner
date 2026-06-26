"""Artifact summary helpers for Advanced Diagnostics."""

from __future__ import annotations

from metrology_process_planner.domains.artifacts.artifact_visibility import (
    artifact_visible_for_session,
)
from metrology_process_planner.domains.session import (
    ArtifactRecord,
    ArtifactStatus,
    ModeRegistry,
    SessionRecord,
)
from metrology_process_planner.workflows.artifacts import built_in_generator_registry
from metrology_process_planner.workflows.artifacts.repair_support import (
    is_process_only_repair_artifact,
)


def artifact_summary(
    session: SessionRecord,
    mode_registry: ModeRegistry | None = None,
) -> str:
    """Return visible artifact status counts for the diagnostics summary."""

    artifacts = _visible_artifacts(session, mode_registry)
    if not artifacts:
        return "0 total"
    counts: dict[str, int] = {}
    for artifact in artifacts:
        counts[artifact.status.value] = counts.get(artifact.status.value, 0) + 1
    status_text = "; ".join(f"{key}={counts[key]}" for key in sorted(counts))
    return f"{len(artifacts)} total; {status_text}"


def artifact_repair_queue_summary(
    session: SessionRecord,
    mode_registry: ModeRegistry | None = None,
) -> str:
    """Return visible repair-candidate counts for the diagnostics summary."""

    count = sum(
        1
        for artifact in _visible_artifacts(session, mode_registry)
        if _is_repair_candidate(session, artifact, mode_registry)
    )
    return f"{count} candidate(s)"


def artifact_generator_summary() -> str:
    """Return registered artifact generator counts."""

    registry = built_in_generator_registry()
    registrations = registry.registrations()
    headless = sum(1 for item in registrations if item.can_run_headless)
    live = sum(1 for item in registrations if item.requires_live_layout)
    return f"{len(registrations)} registered; {headless} headless; {live} live-layout"


def missing_artifact_count(
    session: SessionRecord,
    mode_registry: ModeRegistry | None = None,
) -> int:
    """Return the count of visible canonical artifacts marked missing."""

    return sum(
        1
        for artifact in _visible_artifacts(session, mode_registry)
        if artifact.status is ArtifactStatus.MISSING
    )


def _visible_artifacts(
    session: SessionRecord,
    mode_registry: ModeRegistry | None,
) -> tuple[ArtifactRecord, ...]:
    return tuple(
        artifact
        for artifact in (session.artifacts or {}).values()
        if artifact_visible_for_session(session, artifact, mode_registry)
    )


def _is_repair_candidate(
    session: SessionRecord,
    artifact: ArtifactRecord,
    mode_registry: ModeRegistry | None,
) -> bool:
    return artifact.status.value in {"missing", "stale", "failed", "placeholder"} and not (
        is_process_only_repair_artifact(session, artifact, mode_registry)
    )
