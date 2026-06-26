"""Placeholder artifact helpers."""

from __future__ import annotations

from dataclasses import replace

from metrology_process_planner.domains.session import (
    ArtifactRecord,
    ArtifactStatus,
)


def placeholder_artifact(
    artifact: ArtifactRecord,
    reason: str,
    suggestion: str,
    affected_output: str = "",
) -> ArtifactRecord:
    """Return a visible placeholder artifact record for blocked generation."""

    extensions = dict(artifact.extensions or {})
    placeholder = dict(extensions.get("placeholder", {}))
    placeholder.update(
        {
            "reason": reason,
            "repair_suggestion": suggestion,
            "affected_output": affected_output or artifact.id,
        }
    )
    extensions["placeholder"] = placeholder
    repair = replace(
        artifact.repair,
        placeholder_reason=reason,
        repair_suggestion=suggestion or artifact.repair.repair_suggestion,
    )
    return replace(
        artifact,
        status=ArtifactStatus.PLACEHOLDER,
        repair=repair,
        extensions=extensions,
    )
