"""Setup and alignment records for session initialization."""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
from typing import Any, Optional

from metrology_process_planner.domains.geometry import Point


@dataclass(frozen=True)
class SetupItemRecord:
    """Typed setup item that can own artifacts and warnings."""

    id: str
    item_type: str
    label: str = ""
    status: str = "ready"
    artifact_refs: Optional[Mapping[str, str]] = None
    metadata: Optional[Mapping[str, Any]] = None
    warning_ids: tuple[str, ...] = ()

    def __post_init__(self) -> None:
        if self.artifact_refs is None:
            object.__setattr__(self, "artifact_refs", {})
        if self.metadata is None:
            object.__setattr__(self, "metadata", {})

    def to_dict(self) -> dict[str, Any]:
        """Serialize setup item metadata."""

        return {
            "id": self.id,
            "item_type": self.item_type,
            "label": self.label,
            "status": self.status,
            "artifact_refs": dict(self.artifact_refs or {}),
            "metadata": dict(self.metadata or {}),
            "warning_ids": list(self.warning_ids),
        }

    @classmethod
    def from_dict(cls, data: Mapping[str, Any]) -> SetupItemRecord:
        """Build setup item metadata from saved data."""

        return cls(
            id=str(data["id"]),
            item_type=str(data.get("item_type", "")),
            label=str(data.get("label", "")),
            status=str(data.get("status", "ready")),
            artifact_refs=dict(data.get("artifact_refs", {})),
            metadata=dict(data.get("metadata", {})),
            warning_ids=tuple(str(item) for item in data.get("warning_ids", ())),
        )


@dataclass(frozen=True)
class OriginRecord:
    """User-defined or global origin used to interpret capture coordinates."""

    point: Point
    label: str = "origin"
    coordinate_mode: str = "user_defined"

    def to_dict(self) -> dict[str, Any]:
        """Serialize the origin to JSON-compatible data."""

        return {
            "point": self.point.to_dict(),
            "label": self.label,
            "coordinate_mode": self.coordinate_mode,
        }

    @classmethod
    def from_dict(cls, data: Mapping[str, Any]) -> OriginRecord:
        """Build an origin record from saved JSON-compatible data."""

        return cls(
            point=Point.from_dict(data["point"]),
            label=str(data.get("label", "origin")),
            coordinate_mode=str(data.get("coordinate_mode", "user_defined")),
        )


@dataclass(frozen=True)
class AlignmentRecord:
    """A saved alignment mark used during setup and later review."""

    id: str
    point: Point
    label: str = ""
    image_artifact_path: Optional[str] = None
    artifact_refs: Optional[Mapping[str, str]] = None

    def __post_init__(self) -> None:
        if self.artifact_refs is None:
            object.__setattr__(self, "artifact_refs", {})

    def to_dict(self) -> dict[str, Any]:
        """Serialize the alignment mark to JSON-compatible data."""

        return {
            "id": self.id,
            "point": self.point.to_dict(),
            "label": self.label,
            "image_artifact_path": self.image_artifact_path,
            "artifact_refs": dict(self.artifact_refs or {}),
        }

    @classmethod
    def from_dict(cls, data: Mapping[str, Any]) -> AlignmentRecord:
        """Build an alignment mark from saved JSON-compatible data."""

        return cls(
            id=str(data["id"]),
            point=Point.from_dict(data["point"]),
            label=str(data.get("label", "")),
            image_artifact_path=_optional_str(data.get("image_artifact_path")),
            artifact_refs=dict(data.get("artifact_refs", {})),
        )


@dataclass(frozen=True)
class SetupState:
    """Durable setup progress for origin and alignment workflows."""

    coordinate_mode: str = "global"
    origin: Optional[OriginRecord] = None
    alignments: tuple[AlignmentRecord, ...] = ()
    items: tuple[SetupItemRecord, ...] = ()
    is_capture_ready: bool = False

    def to_dict(self) -> dict[str, Any]:
        """Serialize setup progress to JSON-compatible data."""

        return {
            "coordinate_mode": self.coordinate_mode,
            "origin": self.origin.to_dict() if self.origin is not None else None,
            "alignments": [alignment.to_dict() for alignment in self.alignments],
            "items": [item.to_dict() for item in self.items],
            "is_capture_ready": self.is_capture_ready,
        }

    @classmethod
    def from_dict(cls, data: Mapping[str, Any]) -> SetupState:
        """Build setup progress from saved JSON-compatible data."""

        origin_data = data.get("origin")
        return cls(
            coordinate_mode=str(data.get("coordinate_mode", "global")),
            origin=OriginRecord.from_dict(origin_data) if origin_data is not None else None,
            alignments=tuple(
                AlignmentRecord.from_dict(item) for item in data.get("alignments", ())
            ),
            items=tuple(SetupItemRecord.from_dict(item) for item in data.get("items", ())),
            is_capture_ready=bool(data.get("is_capture_ready", False)),
        )


def _optional_str(value: Any) -> Optional[str]:
    return None if value is None else str(value)
