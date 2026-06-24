"""Protocols for the KLayout adapter boundary."""

from __future__ import annotations

from pathlib import Path
from typing import Protocol

from metrology_process_planner.domains.geometry import Box, Point
from metrology_process_planner.workflows.overlays import OverlayCommand


class LayoutViewPort(Protocol):
    """Minimal layout-view capability needed by workflows."""

    def current_box(self) -> Box:
        """Return the currently visible layout box."""

    def center_on(self, point: Point) -> None:
        """Move the layout viewport to a point."""

    def export_image(self, bounds: Box, destination: Path) -> None:
        """Export a raster image for the requested bounds."""


class CaptureTool(Protocol):
    """Minimal capture-tool capability needed by workflows."""

    def activate_box_capture(self) -> None:
        """Activate a box capture gesture in the layout view."""

    def activate_line_capture(self) -> None:
        """Activate a line capture gesture in the layout view."""

    def activate_point_capture(self) -> None:
        """Activate a point capture gesture in the layout view."""


class CaptureGestureSource(Protocol):
    """KLayout gesture source that can be armed without owning workflows."""

    def arm_box_capture(self) -> None:
        """Arm Shift-drag box capture gestures."""

    def arm_line_capture(self) -> None:
        """Arm Shift-drag line capture gestures."""

    def arm_point_capture(self) -> None:
        """Arm Shift-click point capture gestures."""

    def disarm_capture(self) -> None:
        """Return the layout view to normal navigation behavior."""


class OverlayCommandSink(Protocol):
    """KLayout overlay backend contract for canvas overlay commands."""

    def apply(self, command: OverlayCommand) -> None:
        """Apply one overlay command without mutating source layout shapes."""
