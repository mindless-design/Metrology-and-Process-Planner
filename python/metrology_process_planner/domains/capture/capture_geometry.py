"""Capture geometry records and validation."""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
from enum import Enum
from typing import Any, Optional

from metrology_process_planner.domains.capture.capture_features import normalized_feature_payload
from metrology_process_planner.domains.capture.capture_geometry_validation import (
    validate_box_geometry,
    validate_feature_geometry,
    validate_line_geometry,
)
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
        object.__setattr__(
            self,
            "features",
            tuple(normalized_feature_payload(feature) for feature in self.features),
        )

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
            "primary": self.primary_metadata(),
            "start": self.start.to_dict() if self.start is not None else None,
            "end": self.end.to_dict() if self.end is not None else None,
            "point": self.point.to_dict() if self.point is not None else None,
            "features": [normalized_feature_payload(feature) for feature in self.features],
            "metadata": dict(self.metadata or {}),
        }

    def primary_metadata(self) -> dict[str, Any] | None:
        """Return complete canonical metadata for the primary box geometry."""

        if self.bounds is None:
            return None
        bounds = self.bounds.normalized()
        metadata = dict(self.metadata or {})
        units = str(metadata.get("units", metadata.get("coordinate_units", "layout")))
        coordinate_mode = str(metadata.get("coordinate_mode", "global"))
        primary: dict[str, Any] = {
            "shape": "box",
            "coordinate_mode": coordinate_mode,
            "units": units,
            "bounds": bounds.to_dict(),
            "center": bounds.center.to_dict(),
            "width": bounds.width,
            "height": bounds.height,
        }
        if origin_ref := metadata.get("origin_ref"):
            primary["origin_ref"] = origin_ref
        if source_layout_ref := metadata.get("source_layout_ref"):
            primary["source_layout_ref"] = source_layout_ref
        if source_cell := metadata.get("source_cell"):
            primary["source_cell"] = source_cell
        return primary

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
                normalized_feature_payload(item)
                for item in data.get("features", ())
                if isinstance(item, Mapping)
            ),
            metadata=dict(data.get("metadata", {})),
        )

    def _validate_box(self) -> tuple[str, ...]:
        return validate_box_geometry(self.bounds)

    def _validate_line(self) -> tuple[str, ...]:
        return validate_line_geometry(self.start, self.end)

    def _validate_composite(self) -> tuple[str, ...]:
        return validate_feature_geometry(self.bounds, self.features)
