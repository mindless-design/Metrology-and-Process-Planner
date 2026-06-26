"""Artifact record and registry domain namespace."""

from __future__ import annotations

from importlib import import_module
from typing import Any

from metrology_process_planner.domains.artifacts.artifact_content import artifact_content_type
from metrology_process_planner.domains.artifacts.artifact_ids import artifact_id
from metrology_process_planner.domains.artifacts.artifact_query import (
    artifact_for_role,
    artifact_refs_by_role,
    artifact_refs_for_owner,
    artifacts_for_owner,
    first_display_artifact,
)
from metrology_process_planner.domains.artifacts.artifact_refs_metadata import (
    ArtifactDependencyRef,
    ArtifactFileMetadata,
    ArtifactOwnerRef,
)
from metrology_process_planner.domains.artifacts.artifact_registry import (
    ArtifactPathMode,
    ArtifactRecord,
    ArtifactStatus,
)
from metrology_process_planner.domains.artifacts.artifact_repair_metadata import (
    ArtifactRepairMetadata,
)
from metrology_process_planner.domains.artifacts.legacy_artifacts import legacy_artifacts

_LAZY_EXPORTS = {
    "artifact_visible_for_session": (
        "metrology_process_planner.domains.artifacts.artifact_visibility"
    ),
    "is_process_artifact": "metrology_process_planner.domains.artifacts.artifact_visibility",
}

__all__ = [
    "ArtifactDependencyRef",
    "ArtifactFileMetadata",
    "ArtifactOwnerRef",
    "ArtifactPathMode",
    "ArtifactRecord",
    "ArtifactRepairMetadata",
    "ArtifactStatus",
    "artifact_content_type",
    "artifact_for_role",
    "artifact_id",
    "artifact_refs_by_role",
    "artifact_refs_for_owner",
    "artifact_visible_for_session",
    "artifacts_for_owner",
    "first_display_artifact",
    "is_process_artifact",
    "legacy_artifacts",
]


def __getattr__(name: str) -> Any:
    """Load visibility helpers without creating session-record import cycles."""

    module_name = _LAZY_EXPORTS.get(name)
    if module_name is None:
        raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
    value = getattr(import_module(module_name), name)
    globals()[name] = value
    return value
