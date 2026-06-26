"""KLayout adapter for exporting live layout crop images."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from metrology_process_planner.domains.geometry import Box
from metrology_process_planner.domains.session import ArtifactFileMetadata


class KLayoutLayoutCropExporter:
    """Export capture bounds through the active KLayout view."""

    def __init__(self, pya_module: Any, width_px: int = 1200, height_px: int = 900) -> None:
        self._pya = pya_module
        self._width_px = width_px
        self._height_px = height_px

    def export_image(self, bounds: Box, destination: Path) -> ArtifactFileMetadata | None:
        """Write a crop image for the requested layout bounds."""

        view = _current_view(self._pya)
        if view is None:
            raise RuntimeError("No active KLayout view is available for layout crop export.")
        destination.parent.mkdir(parents=True, exist_ok=True)
        _export_view_image(
            self._pya,
            view,
            bounds.normalized(),
            destination,
            self._width_px,
            self._height_px,
        )
        if not destination.exists():
            raise RuntimeError("KLayout did not write the requested layout crop image.")
        return ArtifactFileMetadata(
            width_px=self._width_px,
            height_px=self._height_px,
            content_type="image/png",
        )


def _current_view(pya: Any) -> Any:
    application = _call_or_value(_call_or_value(pya, "Application"), "instance")
    main_window = _call_or_value(application, "main_window")
    return _call_or_value(main_window, "current_view")


def _export_view_image(
    pya: Any,
    view: Any,
    bounds: Box,
    destination: Path,
    width_px: int,
    height_px: int,
) -> None:
    if hasattr(view, "export_image"):
        view.export_image(bounds, destination)
        return
    target_box = _target_box(pya, bounds)
    if hasattr(view, "save_image_with_options"):
        view.save_image_with_options(str(destination), width_px, height_px, target_box)
        return
    if hasattr(view, "save_image"):
        _center_view(view, bounds)
        view.save_image(str(destination), width_px, height_px)
        return
    raise RuntimeError("The active KLayout view cannot export images.")


def _target_box(pya: Any, bounds: Box) -> Any:
    box_type = getattr(pya, "DBox", None) or getattr(pya, "Box", None)
    if box_type is None:
        return bounds
    return box_type(bounds.left, bounds.bottom, bounds.right, bounds.top)


def _center_view(view: Any, bounds: Box) -> None:
    if hasattr(view, "zoom_box"):
        view.zoom_box(bounds)


def _call_or_value(parent: Any, name: str) -> Any:
    if parent is None or not hasattr(parent, name):
        return None
    value = getattr(parent, name)
    return value() if callable(value) else value
