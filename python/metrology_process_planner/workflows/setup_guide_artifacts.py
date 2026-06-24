"""Setup-guide artifact badge helpers."""

from __future__ import annotations

from collections.abc import Mapping

from metrology_process_planner.domains.session import ArtifactRecord


def artifact_badge(
    artifact_refs: Mapping[str, str] | None,
    artifacts: Mapping[str, ArtifactRecord] | None,
) -> str:
    """Return a compact setup-card artifact availability badge."""

    refs = tuple((artifact_refs or {}).values())
    if not refs:
        return "none"
    statuses = tuple(_status(artifact_id, artifacts) for artifact_id in refs)
    unique = set(statuses)
    if len(unique) == 1:
        return statuses[0]
    if "failed" in unique:
        return "failed"
    if "missing" in unique:
        return "missing"
    if "stale" in unique:
        return "stale"
    return "mixed"


def _status(
    artifact_id: str,
    artifacts: Mapping[str, ArtifactRecord] | None,
) -> str:
    artifact = (artifacts or {}).get(artifact_id)
    if artifact is None:
        return "missing"
    return artifact.status.value
