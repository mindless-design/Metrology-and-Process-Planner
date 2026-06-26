"""Reference-warning helpers for artifact scanning."""

from __future__ import annotations

from dataclasses import replace

from metrology_process_planner.domains.session import ArtifactRecord, SessionRecord, WarningRecord
from metrology_process_planner.workflows.artifacts.signatures import dependency_exists, owner_exists
from metrology_process_planner.workflows.artifacts.warnings import (
    ARTIFACT_DEPENDENCY_MISSING,
    ARTIFACT_OWNER_MISSING,
    artifact_warning,
    upsert_warning,
)


def with_reference_warnings(
    session: SessionRecord,
    artifact: ArtifactRecord,
    warnings: dict[str, WarningRecord],
) -> ArtifactRecord:
    """Return an artifact updated with owner and dependency warnings."""

    current = artifact
    owner = current.owner
    if owner.owner_type and not owner_exists(session, owner.owner_type, owner.owner_id):
        current = _with_warning(
            current,
            artifact_warning(
                current,
                ARTIFACT_OWNER_MISSING,
                f"Artifact owner is missing: {current.label or current.id}",
                f"Owner reference {owner.owner_type}:{owner.owner_id} does not exist.",
                "Replace the owner item or relink this artifact.",
            ),
            warnings,
        )
    return _with_dependency_warnings(session, current, warnings)


def _with_dependency_warnings(
    session: SessionRecord,
    artifact: ArtifactRecord,
    warnings: dict[str, WarningRecord],
) -> ArtifactRecord:
    current = artifact
    for dependency in current.dependencies:
        kind = dependency.kind or ("artifact" if dependency.artifact_id else "")
        dependency_id = dependency.id or dependency.artifact_id
        if kind and dependency_id and not dependency_exists(session, kind, dependency_id):
            current = _with_warning(
                current,
                artifact_warning(
                    current,
                    ARTIFACT_DEPENDENCY_MISSING,
                    f"Artifact dependency is missing: {current.label or current.id}",
                    f"Dependency {kind}:{dependency_id} does not exist.",
                    "Restore the dependency or regenerate a placeholder.",
                ),
                warnings,
            )
    return current


def _with_warning(
    artifact: ArtifactRecord,
    warning: WarningRecord,
    warnings: dict[str, WarningRecord],
) -> ArtifactRecord:
    stored = upsert_warning(warnings, warning)
    ids = tuple(sorted(set(artifact.warning_ids + (stored.id,))))
    return replace(artifact, warning_ids=ids)
