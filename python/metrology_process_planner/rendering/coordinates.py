"""Coordinate mapping helpers for drawing scenes."""

from __future__ import annotations

from dataclasses import dataclass

from metrology_process_planner.domains.geometry import Box, Point
from metrology_process_planner.rendering.primitives import CanvasPoint
from metrology_process_planner.rendering.scene import CanvasSpec


@dataclass(frozen=True)
class CanvasTransform:
    """Map source geometry coordinates into canvas pixel coordinates."""

    bounds: Box
    canvas: CanvasSpec
    y_axis: str = "down"

    def map_point(self, point: Point) -> CanvasPoint:
        """Map one source point into canvas coordinates."""

        bounds = self._normalized_bounds()
        if bounds.width <= 0 or bounds.height <= 0:
            raise ValueError("Cannot map coordinates from empty source bounds.")
        x_ratio = (point.x - bounds.left) / bounds.width
        y_ratio = (point.y - bounds.bottom) / bounds.height
        if self.y_axis == "down":
            y_ratio = 1.0 - y_ratio
        return CanvasPoint(
            x=x_ratio * self.canvas.width_px,
            y=y_ratio * self.canvas.height_px,
        )

    def map_box(self, box: Box) -> tuple[float, float, float, float]:
        """Map source bounds into canvas rectangle coordinates."""

        first = self.map_point(Point(box.left, box.bottom))
        second = self.map_point(Point(box.right, box.top))
        x = min(first.x, second.x)
        y = min(first.y, second.y)
        return (x, y, abs(second.x - first.x), abs(second.y - first.y))

    def _normalized_bounds(self) -> Box:
        return self.bounds.normalized()
