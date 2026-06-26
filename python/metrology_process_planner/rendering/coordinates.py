"""Coordinate mapping helpers for drawing scenes."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Optional

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


@dataclass(frozen=True)
class LayoutToImageTransform:
    """Map layout coordinates to image pixels and back."""

    bounds: Box
    image_width_px: int
    image_height_px: int
    units: str = "layout"
    y_axis: str = "down"
    origin_ref: Optional[Point] = None
    padding_left_px: float = 0.0
    padding_top_px: float = 0.0
    padding_right_px: float = 0.0
    padding_bottom_px: float = 0.0

    def layout_point_to_pixel(self, point: Point) -> CanvasPoint:
        """Map one layout point to image pixel coordinates."""

        bounds = self._validated_bounds()
        local = self._to_layout_origin(point)
        x_ratio = (local.x - bounds.left) / bounds.width
        y_ratio = (local.y - bounds.bottom) / bounds.height
        if self.y_axis == "down":
            y_ratio = 1.0 - y_ratio
        return CanvasPoint(
            x=self.padding_left_px + x_ratio * self._content_width(),
            y=self.padding_top_px + y_ratio * self._content_height(),
        )

    def layout_line_to_pixel(self, line: tuple[Point, Point]) -> tuple[CanvasPoint, CanvasPoint]:
        """Map one layout line to image pixel endpoints."""

        return (
            self.layout_point_to_pixel(line[0]),
            self.layout_point_to_pixel(line[1]),
        )

    def layout_box_to_pixel(self, box: Box) -> tuple[float, float, float, float]:
        """Map one layout box to x, y, width, height pixel coordinates."""

        first = self.layout_point_to_pixel(Point(box.left, box.bottom))
        second = self.layout_point_to_pixel(Point(box.right, box.top))
        return (
            min(first.x, second.x),
            min(first.y, second.y),
            abs(second.x - first.x),
            abs(second.y - first.y),
        )

    def pixel_point_to_layout(self, point: CanvasPoint) -> Point:
        """Map one image pixel coordinate back to layout coordinates."""

        bounds = self._validated_bounds()
        x_ratio = (point.x - self.padding_left_px) / self._content_width()
        y_ratio = (point.y - self.padding_top_px) / self._content_height()
        if self.y_axis == "down":
            y_ratio = 1.0 - y_ratio
        layout = Point(
            x=bounds.left + x_ratio * bounds.width,
            y=bounds.bottom + y_ratio * bounds.height,
        )
        if self.origin_ref is None:
            return layout
        return Point(layout.x + self.origin_ref.x, layout.y + self.origin_ref.y)

    def _to_layout_origin(self, point: Point) -> Point:
        if self.origin_ref is None:
            return point
        return Point(point.x - self.origin_ref.x, point.y - self.origin_ref.y)

    def _validated_bounds(self) -> Box:
        bounds = self.bounds.normalized()
        if bounds.width <= 0 or bounds.height <= 0:
            raise ValueError("Cannot map coordinates from empty source bounds.")
        if self._content_width() <= 0 or self._content_height() <= 0:
            raise ValueError("Cannot map coordinates into an empty image area.")
        if self.y_axis not in {"up", "down"}:
            raise ValueError("Image y-axis must be 'up' or 'down'.")
        return bounds

    def _content_width(self) -> float:
        return self.image_width_px - self.padding_left_px - self.padding_right_px

    def _content_height(self) -> float:
        return self.image_height_px - self.padding_top_px - self.padding_bottom_px
