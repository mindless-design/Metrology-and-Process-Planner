"""Capture geometry records and validation."""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
from enum import Enum
from typing import Any, Optional

from metrology_process_planner.domains.geometry import Box, Point


class GeometryKind(str, Enum):
    """Supported capture gesture shapes."""

    BOX = "box"
    LINE = "line"
    POINT = "point"
    COMPOSITE = "composite"
    GRID = "grid"


@dataclass(frozen=True)
class CaptureGeometry:
    """Geometry captured from the layout view."""

    kind: GeometryKind
    bounds: Optional[Box] = None
    start: Optional[Point] = None
    end: Optional[Point] = None
    point: Optional[Point] = None
    features: tuple[Mapping[str, Any], ...] = ()
    metadata: Optional[Mapping[str, Any]] = None

    def __post_init__(self) -> None:
        if self.metadata is None:
            object.__setattr__(self, "metadata", {})

    @classmethod
    def box(cls, bounds: Box) -> CaptureGeometry:
        """Create box capture geometry from layout bounds."""

        return cls(kind=GeometryKind.BOX, bounds=bounds.normalized())

    @classmethod
    def line(cls, start: Point, end: Point) -> CaptureGeometry:
        """Create line capture geometry from two layout points."""

        return cls(kind=GeometryKind.LINE, start=start, end=end)

    @classmethod
    def point_capture(cls, point: Point) -> CaptureGeometry:
        """Create point capture geometry from one layout point."""

        return cls(kind=GeometryKind.POINT, point=point)

    def validate(self) -> tuple[str, ...]:
        """Return user-visible warnings for incomplete or invalid geometry."""

        if self.kind is GeometryKind.BOX:
            return self._validate_box()
        if self.kind is GeometryKind.LINE:
            return self._validate_line()
        if self.kind in {GeometryKind.COMPOSITE, GeometryKind.GRID}:
            return self._validate_composite()
        if self.point is None:
            return ("Point capture geometry requires a point.",)
        return ()

    def to_dict(self) -> dict[str, Any]:
        """Serialize geometry to JSON-compatible data."""

        return {
            "kind": self.kind.value,
            "bounds": self.bounds.to_dict() if self.bounds is not None else None,
            "start": self.start.to_dict() if self.start is not None else None,
            "end": self.end.to_dict() if self.end is not None else None,
            "point": self.point.to_dict() if self.point is not None else None,
            "features": [dict(feature) for feature in self.features],
            "metadata": dict(self.metadata or {}),
        }

    @classmethod
    def from_dict(cls, data: Mapping[str, Any]) -> CaptureGeometry:
        """Build capture geometry from saved JSON-compatible data."""

        return cls(
            kind=GeometryKind(str(data["kind"])),
            bounds=Box.from_dict(data["bounds"]) if data.get("bounds") is not None else None,
            start=Point.from_dict(data["start"]) if data.get("start") is not None else None,
            end=Point.from_dict(data["end"]) if data.get("end") is not None else None,
            point=Point.from_dict(data["point"]) if data.get("point") is not None else None,
            features=tuple(
                dict(item) for item in data.get("features", ()) if isinstance(item, Mapping)
            ),
            metadata=dict(data.get("metadata", {})),
        )

    def _validate_box(self) -> tuple[str, ...]:
        if self.bounds is None:
            return ("Box capture geometry requires bounds.",)
        if self.bounds.width <= 0 or self.bounds.height <= 0:
            return ("Box capture geometry requires positive width and height.",)
        return ()

    def _validate_line(self) -> tuple[str, ...]:
        if self.start is None or self.end is None:
            return ("Line capture geometry requires start and end points.",)
        if self.start == self.end:
            return ("Line capture geometry requires distinct start and end points.",)
        return ()

    def _validate_composite(self) -> tuple[str, ...]:
        if self.bounds is None and not self.features:
            return ("Composite or grid capture geometry requires bounds or features.",)
        return ()
