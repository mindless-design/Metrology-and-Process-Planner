"""Canonical artifact registry records."""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
from enum import Enum
from typing import Any, Optional

from metrology_process_planner.domains.artifacts.artifact_refs_metadata import (
    ArtifactDependencyRef,
    ArtifactFileMetadata,
    ArtifactOwnerRef,
)
from metrology_process_planner.domains.artifacts.artifact_repair_metadata import (
    ArtifactRepairMetadata,
)
from metrology_process_planner.domains.session.constants import utc_now_iso

__all__ = [
    "ArtifactDependencyRef",
    "ArtifactFileMetadata",
    "ArtifactOwnerRef",
    "ArtifactPathMode",
    "ArtifactRecord",
    "ArtifactRepairMetadata",
    "ArtifactStatus",
]


class ArtifactStatus(str, Enum):
    """Durable artifact lifecycle states stored in canonical session JSON."""

    PRESENT = "present"
    MISSING = "missing"
    STALE = "stale"
    FAILED = "failed"
    PLACEHOLDER = "placeholder"
    EXTERNAL = "external"
    PENDING = "pending"
    PENDING_SOLVER = "pending_solver"
    SUPERSEDED = "superseded"
    INTENTIONALLY_IGNORED = "intentionally_ignored"
class ArtifactPathMode(str, Enum):
    """How an artifact path should be resolved."""

    SESSION_RELATIVE = "session_relative"
    RELATIVE_TO_SESSION_JSON = "relative_to_session_json"
    EXTERNAL = "external"
@dataclass(frozen=True)
class ArtifactRecord:
    """Canonical first-class artifact registry record."""

    id: str
    type: str
    label: str
    relative_path: str
    owner: ArtifactOwnerRef
    path_mode: ArtifactPathMode = ArtifactPathMode.SESSION_RELATIVE
    status: ArtifactStatus = ArtifactStatus.PRESENT
    dependencies: tuple[ArtifactDependencyRef, ...] = ()
    generated_at: str = ""
    generator: str = ""
    generator_version: str = ""
    file: ArtifactFileMetadata = ArtifactFileMetadata()
    repair: ArtifactRepairMetadata = ArtifactRepairMetadata()
    warning_ids: tuple[str, ...] = ()
    content_hash: str = ""
    dependency_signature: str = ""
    trace_ids: Optional[Mapping[str, str]] = None
    extensions: Optional[Mapping[str, Any]] = None

    def __post_init__(self) -> None:
        if not self.generated_at:
            object.__setattr__(self, "generated_at", utc_now_iso())
        if self.trace_ids is None:
            object.__setattr__(self, "trace_ids", {})
        if self.extensions is None:
            object.__setattr__(self, "extensions", {})

    def to_dict(self) -> dict[str, Any]:
        """Serialize the artifact registry record."""

        return {
            "id": self.id,
            "type": self.type,
            "label": self.label,
            "relative_path": self.relative_path,
            "path_mode": self.path_mode.value,
            "status": self.status.value,
            "owner": self.owner.to_dict(),
            "dependencies": [dependency.to_dict() for dependency in self.dependencies],
            "generated_at": self.generated_at,
            "generator": self.generator,
            "generator_version": self.generator_version,
            "file": self.file.to_dict(),
            "repair": self.repair.to_dict(),
            "warning_ids": list(self.warning_ids),
            "content_hash": self.content_hash,
            "dependency_signature": self.dependency_signature,
            "trace_ids": dict(self.trace_ids or {}),
            "extensions": dict(self.extensions or {}),
        }

    @classmethod
    def from_dict(cls, data: Mapping[str, Any]) -> ArtifactRecord:
        """Build an artifact registry record from saved data."""

        path_mode = _path_mode(str(data.get("path_mode", ArtifactPathMode.SESSION_RELATIVE.value)))
        return cls(
            id=str(data["id"]),
            type=str(data.get("type", "artifact")),
            label=str(data.get("label", "")),
            relative_path=str(data.get("relative_path", data.get("path", ""))),
            path_mode=path_mode,
            status=ArtifactStatus(str(data.get("status", ArtifactStatus.PRESENT.value))),
            owner=ArtifactOwnerRef.from_dict(data.get("owner", {})),
            dependencies=tuple(
                ArtifactDependencyRef.from_dict(item)
                for item in data.get("dependencies", ())
            ),
            generated_at=str(data.get("generated_at", "")),
            generator=str(data.get("generator", "")),
            generator_version=str(data.get("generator_version", "")),
            file=ArtifactFileMetadata.from_dict(data.get("file", {})),
            repair=ArtifactRepairMetadata.from_dict(data.get("repair", {})),
            warning_ids=tuple(str(item) for item in data.get("warning_ids", ())),
            content_hash=str(data.get("content_hash", "")),
            dependency_signature=str(data.get("dependency_signature", "")),
            trace_ids=dict(data.get("trace_ids", {})),
            extensions=dict(data.get("extensions", {})),
        )


def _path_mode(value: str) -> ArtifactPathMode:
    if value == "relative_to_session_json":
        return ArtifactPathMode.RELATIVE_TO_SESSION_JSON
    return ArtifactPathMode(value)
