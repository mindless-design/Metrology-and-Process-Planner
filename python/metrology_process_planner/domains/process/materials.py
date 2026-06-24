"""Material and layout-layer references for process recipes."""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True)
class Material:
    """A process material with display properties."""

    id: str
    name: str
    color: str
    visible: bool = True

    def to_dict(self) -> dict[str, Any]:
        """Serialize the material to JSON-compatible data."""

        return {
            "id": self.id,
            "name": self.name,
            "color": self.color,
            "visible": self.visible,
        }

    @classmethod
    def from_dict(cls, data: Mapping[str, Any]) -> Material:
        """Build a material from saved JSON-compatible data."""

        return cls(
            id=str(data["id"]),
            name=str(data.get("name", data["id"])),
            color=str(data.get("color", "#888888")),
            visible=bool(data.get("visible", True)),
        )


@dataclass(frozen=True)
class LayerReference:
    """A process step reference to a KLayout layer/datatype pair."""

    source: str
    layer: int
    datatype: int = 0
    name: str = ""

    def to_dict(self) -> dict[str, Any]:
        """Serialize the layer reference to JSON-compatible data."""

        return {
            "source": self.source,
            "layer": self.layer,
            "datatype": self.datatype,
            "name": self.name,
        }

    @classmethod
    def from_dict(cls, data: Mapping[str, Any]) -> LayerReference:
        """Build a layer reference from saved JSON-compatible data."""

        return cls(
            source=str(data.get("source", "layout")),
            layer=int(data["layer"]),
            datatype=int(data.get("datatype", 0)),
            name=str(data.get("name", "")),
        )

