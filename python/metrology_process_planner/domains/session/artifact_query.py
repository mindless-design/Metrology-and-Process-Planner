"""Typed read helpers for the canonical artifact registry."""

from __future__ import annotations

from collections.abc import Iterable, Mapping

from metrology_process_planner.domains.session.artifact_registry import ArtifactRecord


def artifacts_for_owner(
    artifacts: Mapping[str, ArtifactRecord],
    owner_type: str,
    owner_id: str,
) -> tuple[ArtifactRecord, ...]:
    """Return artifacts owned by one canonical session record."""

    return tuple(
        artifact
        for artifact in artifacts.values()
        if artifact.owner.owner_type == owner_type and artifact.owner.owner_id == owner_id
    )


def artifact_refs_by_role(artifacts: Iterable[ArtifactRecord]) -> dict[str, str]:
    """Return local owner convenience refs from canonical artifact records."""

    return {artifact.owner.role: artifact.id for artifact in artifacts}


def artifact_refs_for_owner(
    artifacts: Mapping[str, ArtifactRecord],
    owner_type: str,
    owner_id: str,
) -> dict[str, str]:
    """Return owner artifact refs from the canonical registry."""

    return artifact_refs_by_role(artifacts_for_owner(artifacts, owner_type, owner_id))


def first_display_artifact(
    artifacts: Mapping[str, ArtifactRecord],
    owner_type: str,
    owner_id: str,
) -> ArtifactRecord | None:
    """Return the preferred image-like artifact for an owner."""

    owner_artifacts = artifacts_for_owner(artifacts, owner_type, owner_id)
    role_order = ("crop", "pending_crop", "layout_annotation_png", "layout_annotation_svg")
    for role in role_order:
        artifact = artifact_for_role(owner_artifacts, role)
        if artifact is not None:
            return artifact
    for artifact in owner_artifacts:
        if artifact.type in {"image", "svg"}:
            return artifact
    return None


def artifact_for_role(
    artifacts: Iterable[ArtifactRecord],
    role: str,
) -> ArtifactRecord | None:
    """Return the first artifact with a matching owner role."""

    for artifact in artifacts:
        if artifact.owner.role == role:
            return artifact
    return None
