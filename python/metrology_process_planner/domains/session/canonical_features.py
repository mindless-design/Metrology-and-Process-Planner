"""Canonical session geometry feature records."""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
from typing import Any, Optional


@dataclass(frozen=True)
class GeometryFeature:
    """Named geometry feature used by composite and mode-specific captures."""

    id: str
    label: str
    geometry: Mapping[str, Any]
    parent_id: Optional[str] = None
    role: str = ""
    extensions: Optional[Mapping[str, Any]] = None

    def __post_init__(self) -> None:
        if self.extensions is None:
            object.__setattr__(self, "extensions", {})

    def to_dict(self) -> dict[str, Any]:
        """Serialize geometry feature metadata."""

        return {
            "id": self.id,
            "label": self.label,
            "role": self.role,
            "parent_id": self.parent_id,
            "geometry": dict(self.geometry),
            "extensions": dict(self.extensions or {}),
        }

    @classmethod
    def from_dict(cls, data: Mapping[str, Any]) -> GeometryFeature:
        """Build geometry feature metadata from saved data."""

        geometry = data.get("geometry", {})
        return cls(
            id=str(data["id"]),
            label=str(data.get("label", "")),
            role=str(data.get("role", "")),
            parent_id=None if data.get("parent_id") is None else str(data.get("parent_id")),
            geometry=dict(geometry) if isinstance(geometry, Mapping) else {},
            extensions=dict(data.get("extensions", {})),
        )
