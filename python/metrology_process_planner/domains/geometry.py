"""Geometry value objects used by captures and measurements."""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
from math import hypot
from typing import Any


@dataclass(frozen=True)
class Point:
    """A two-dimensional layout point."""

    x: float
    y: float

    def distance_to(self, other: Point) -> float:
        """Return Euclidean distance to another point."""

        return hypot(other.x - self.x, other.y - self.y)

    def to_dict(self) -> dict[str, float]:
        """Serialize the point to JSON-compatible data."""

        return {"x": self.x, "y": self.y}

    @classmethod
    def from_dict(cls, data: Mapping[str, Any]) -> Point:
        """Build a point from saved JSON-compatible data."""

        return cls(x=float(data["x"]), y=float(data["y"]))


@dataclass(frozen=True)
class Box:
    """Axis-aligned layout bounds."""

    left: float
    bottom: float
    right: float
    top: float

    def normalized(self) -> Box:
        """Return bounds with ordered horizontal and vertical limits."""

        return Box(
            left=min(self.left, self.right),
            bottom=min(self.bottom, self.top),
            right=max(self.left, self.right),
            top=max(self.bottom, self.top),
        )

    @property
    def width(self) -> float:
        """Return normalized box width."""

        return self.normalized().right - self.normalized().left

    @property
    def height(self) -> float:
        """Return normalized box height."""

        return self.normalized().top - self.normalized().bottom

    @property
    def center(self) -> Point:
        """Return the center point of the normalized box."""

        box = self.normalized()
        return Point(x=(box.left + box.right) / 2.0, y=(box.bottom + box.top) / 2.0)

    def contains_point(self, point: Point) -> bool:
        """Return whether the normalized box contains a point."""

        box = self.normalized()
        return box.left <= point.x <= box.right and box.bottom <= point.y <= box.top

    def contains_segment(self, start: Point, end: Point) -> bool:
        """Return whether the normalized box contains a line segment."""

        return self.contains_point(start) and self.contains_point(end)

    def to_dict(self) -> dict[str, float]:
        """Serialize the normalized box to JSON-compatible data."""

        box = self.normalized()
        return {
            "left": box.left,
            "bottom": box.bottom,
            "right": box.right,
            "top": box.top,
        }

    @classmethod
    def from_dict(cls, data: Mapping[str, Any]) -> Box:
        """Build normalized bounds from saved JSON-compatible data."""

        return cls(
            left=float(data["left"]),
            bottom=float(data["bottom"]),
            right=float(data["right"]),
            top=float(data["top"]),
        ).normalized()
