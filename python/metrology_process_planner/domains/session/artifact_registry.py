"""Canonical artifact registry records."""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
from enum import Enum
from typing import Any, Optional

from metrology_process_planner.domains.session.constants import utc_now_iso
from metrology_process_planner.domains.session.record_values import optional_int, optional_str


class ArtifactStatus(str, Enum):
    """Durable artifact lifecycle states stored in canonical session JSON."""

    PRESENT = "present"
    MISSING = "missing"
    STALE = "stale"
    FAILED = "failed"
    EXTERNAL = "external"
    PENDING = "pending"
    SUPERSEDED = "superseded"
    PLACEHOLDER = "placeholder"
    PENDING_SOLVER = "pending_solver"

class ArtifactPathMode(str, Enum):
    """How an artifact path should be resolved."""

    SESSION_RELATIVE = "session_relative"
    EXTERNAL = "external"

@dataclass(frozen=True)
class ArtifactOwnerRef:
    """Reference to the record that owns an artifact."""

    owner_type: str
    owner_id: str
    role: str

    def to_dict(self) -> dict[str, str]:
        """Serialize owner metadata."""

        return {
            "owner_type": self.owner_type,
            "owner_id": self.owner_id,
            "role": self.role,
        }

    @classmethod
    def from_dict(cls, data: Mapping[str, Any]) -> ArtifactOwnerRef:
        """Build owner metadata from JSON-compatible data."""

        return cls(
            owner_type=str(data.get("owner_type", "")),
            owner_id=str(data.get("owner_id", "")),
            role=str(data.get("role", "")),
        )


@dataclass(frozen=True)
class ArtifactDependencyRef:
    """Reference to an artifact dependency."""

    artifact_id: str
    role: str = ""

    def to_dict(self) -> dict[str, str]:
        """Serialize dependency metadata."""
        return {"artifact_id": self.artifact_id, "role": self.role}

    @classmethod
    def from_dict(cls, data: Mapping[str, Any]) -> ArtifactDependencyRef:
        """Build dependency metadata from saved data."""

        return cls(
            artifact_id=str(data.get("artifact_id", "")),
            role=str(data.get("role", "")),
        )


@dataclass(frozen=True)
class ArtifactFileMetadata:
    """Portable file metadata for a generated artifact."""

    sha256: Optional[str] = None
    size_bytes: Optional[int] = None
    width_px: Optional[int] = None
    height_px: Optional[int] = None
    content_type: str = ""

    def to_dict(self) -> dict[str, Any]:
        """Serialize file metadata."""

        return {
            "sha256": self.sha256,
            "size_bytes": self.size_bytes,
            "width_px": self.width_px,
            "height_px": self.height_px,
            "content_type": self.content_type,
        }

    @classmethod
    def from_dict(cls, data: Mapping[str, Any]) -> ArtifactFileMetadata:
        """Build file metadata from JSON-compatible data."""

        return cls(
            sha256=optional_str(data.get("sha256")),
            size_bytes=optional_int(data.get("size_bytes")),
            width_px=optional_int(data.get("width_px")),
            height_px=optional_int(data.get("height_px")),
            content_type=str(data.get("content_type", "")),
        )


@dataclass(frozen=True)
class ArtifactRepairMetadata:
    """Repair metadata surfaced by editor and diagnostics workflows."""

    repair_action: str = ""
    repair_suggestion: str = ""
    last_attempt_at: Optional[str] = None
    last_error: str = ""

    def to_dict(self) -> dict[str, Any]:
        """Serialize repair metadata."""

        return {
            "repair_action": self.repair_action,
            "repair_suggestion": self.repair_suggestion,
            "last_attempt_at": self.last_attempt_at,
            "last_error": self.last_error,
        }

    @classmethod
    def from_dict(cls, data: Mapping[str, Any]) -> ArtifactRepairMetadata:
        """Build repair metadata from JSON-compatible data."""

        return cls(
            repair_action=str(data.get("repair_action", "")),
            repair_suggestion=str(data.get("repair_suggestion", "")),
            last_attempt_at=optional_str(data.get("last_attempt_at")),
            last_error=str(data.get("last_error", "")),
        )


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
    file: ArtifactFileMetadata = ArtifactFileMetadata()
    repair: ArtifactRepairMetadata = ArtifactRepairMetadata()
    warning_ids: tuple[str, ...] = ()
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
            "file": self.file.to_dict(),
            "repair": self.repair.to_dict(),
            "warning_ids": list(self.warning_ids),
            "trace_ids": dict(self.trace_ids or {}),
            "extensions": dict(self.extensions or {}),
        }

    @classmethod
    def from_dict(cls, data: Mapping[str, Any]) -> ArtifactRecord:
        """Build an artifact registry record from saved data."""

        path_mode = data.get("path_mode", ArtifactPathMode.SESSION_RELATIVE.value)
        return cls(
            id=str(data["id"]),
            type=str(data.get("type", "artifact")),
            label=str(data.get("label", "")),
            relative_path=str(data.get("relative_path", data.get("path", ""))),
            path_mode=ArtifactPathMode(str(path_mode)),
            status=ArtifactStatus(str(data.get("status", ArtifactStatus.PRESENT.value))),
            owner=ArtifactOwnerRef.from_dict(data.get("owner", {})),
            dependencies=tuple(
                ArtifactDependencyRef.from_dict(item)
                for item in data.get("dependencies", ())
            ),
            generated_at=str(data.get("generated_at", "")),
            generator=str(data.get("generator", "")),
            file=ArtifactFileMetadata.from_dict(data.get("file", {})),
            repair=ArtifactRepairMetadata.from_dict(data.get("repair", {})),
            warning_ids=tuple(str(item) for item in data.get("warning_ids", ())),
            trace_ids=dict(data.get("trace_ids", {})),
            extensions=dict(data.get("extensions", {})),
        )
