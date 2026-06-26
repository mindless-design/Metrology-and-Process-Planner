"""Artifact owner, dependency, and file metadata records."""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
from typing import Any, Optional

from metrology_process_planner.domains.session.record_values import optional_int, optional_str


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

    artifact_id: str = ""
    role: str = ""
    kind: str = ""
    id: str = ""
    signature: str = ""

    def to_dict(self) -> dict[str, str]:
        """Serialize dependency metadata."""

        return {
            "artifact_id": self.artifact_id,
            "role": self.role,
            "kind": self.kind,
            "id": self.id,
            "signature": self.signature,
        }

    @classmethod
    def from_dict(cls, data: Mapping[str, Any]) -> ArtifactDependencyRef:
        """Build dependency metadata from saved data."""

        return cls(
            artifact_id=str(data.get("artifact_id", "")),
            role=str(data.get("role", "")),
            kind=str(data.get("kind", "")),
            id=str(data.get("id", data.get("artifact_id", ""))),
            signature=str(data.get("signature", "")),
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
