"""KLayout adapter for binding the active layout view to a session."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from metrology_process_planner.app.session_layout_adapter import LayoutBindingSelection
from metrology_process_planner.domains.session import SourceLayoutContext


class KLayoutSessionLayoutAdapter:
    """Read current KLayout layout/view metadata without mutating layout data."""

    def __init__(self, pya_module: Any) -> None:
        self._pya = pya_module

    def select_current_layout(self) -> LayoutBindingSelection:
        """Return metadata for the active KLayout cell view."""

        cell_view = _active_cell_view(self._pya)
        if cell_view is None:
            return LayoutBindingSelection(
                status="unavailable",
                message="No active KLayout layout view is available.",
            )
        layout = _call_or_value(cell_view, "layout")
        if layout is None:
            return LayoutBindingSelection(
                status="unavailable",
                message="The active KLayout view has no layout.",
            )
        layout_path = _layout_path(layout)
        top_cell = _top_cell_name(cell_view, layout)
        source_layout = SourceLayoutContext(
            layout_path=layout_path,
            layout_name=Path(layout_path).name if layout_path else _layout_name(layout),
            top_cell=top_cell,
            layout_fingerprint=_layout_fingerprint(layout_path, top_cell, layout),
            klayout_version=_klayout_version(self._pya),
        )
        return LayoutBindingSelection.selected(source_layout)


def _active_cell_view(pya: Any) -> Any:
    application = _call_or_value(_call_or_value(pya, "Application"), "instance")
    main_window = _call_or_value(application, "main_window")
    view = _call_or_value(main_window, "current_view")
    return _call_or_value(view, "active_cellview")


def _layout_path(layout: Any) -> str:
    for name in ("filename", "file_name", "path"):
        value = _call_or_value(layout, name)
        if value:
            return str(value)
    return ""


def _layout_name(layout: Any) -> str:
    name = _call_or_value(layout, "name")
    return str(name) if name else ""


def _top_cell_name(cell_view: Any, layout: Any) -> str:
    cell = _call_or_value(cell_view, "cell")
    name = _call_or_value(cell, "name")
    if name:
        return str(name)
    top_cell = _call_or_value(layout, "top_cell")
    name = _call_or_value(top_cell, "name")
    return str(name) if name else ""


def _layout_fingerprint(layout_path: str, top_cell: str, layout: Any) -> str:
    path = Path(layout_path) if layout_path else None
    if path is not None and path.exists():
        stat = path.stat()
        return f"{path.resolve()}|{stat.st_size}|{stat.st_mtime_ns}|{top_cell}"
    dbu = _call_or_value(layout, "dbu")
    cell_count = _call_or_value(layout, "cells")
    return "|".join(str(item) for item in (layout_path, top_cell, dbu or "", cell_count or ""))


def _klayout_version(pya: Any) -> str:
    application = _call_or_value(_call_or_value(pya, "Application"), "instance")
    version = _call_or_value(application, "version")
    if version:
        return str(version)
    version = _call_or_value(pya, "version")
    return str(version) if version else ""


def _call_or_value(parent: Any, name: str) -> Any:
    if parent is None or not hasattr(parent, name):
        return None
    value = getattr(parent, name)
    return value() if callable(value) else value
