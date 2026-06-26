"""KLayout picker adapter for session document paths."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from metrology_process_planner.app.session_path_adapter import (
    NewSessionSelection,
    PathSelection,
)
from metrology_process_planner.domains.session import (
    ModeRegistry,
    SessionMode,
    SessionModeId,
    built_in_mode_registry,
)


class KLayoutSessionPathAdapter:
    """Collect session paths from KLayout/Qt dialogs."""

    def __init__(self, pya_module: Any, mode_registry: ModeRegistry | None = None) -> None:
        self._pya = pya_module
        self._mode_registry = mode_registry or built_in_mode_registry()

    def select_new_session(self) -> NewSessionSelection:
        """Ask for an output folder and mode for a new session."""

        folder = _existing_directory(self._pya, "Choose Process Planner Session Folder")
        if not folder:
            return NewSessionSelection(message="New Session cancelled.")
        mode = _mode_choice(self._pya, self._mode_registry)
        return NewSessionSelection.selected(Path(folder), Path(folder).name, mode)

    def select_open_session(self) -> PathSelection:
        """Ask for an existing session JSON file."""

        path = _open_file(self._pya, "Open Process Planner Session", "Session JSON (*.json)")
        if not path:
            return PathSelection(message="Open Session cancelled.")
        return PathSelection.selected(path)

    def select_recent_session(self, recent_paths: tuple[Path, ...]) -> PathSelection:
        """Ask which recent session should be opened."""

        if not recent_paths:
            return PathSelection(status="unavailable", message="No recent sessions are known.")
        chosen = _item_choice(self._pya, "Open Recent Session", tuple(map(str, recent_paths)))
        if not chosen:
            return PathSelection(message="Open Recent cancelled.")
        return PathSelection.selected(chosen)

    def select_save_as_destination(self) -> PathSelection:
        """Ask for a destination session JSON path."""

        path = _save_file(self._pya, "Save Process Planner Session As", "Session JSON (*.json)")
        if not path:
            return PathSelection(message="Save Session As cancelled.")
        return PathSelection.selected(path)


def _existing_directory(pya: Any, title: str) -> str:
    dialog = getattr(pya, "QFileDialog", None)
    if dialog is None or not hasattr(dialog, "getExistingDirectory"):
        return ""
    return str(dialog.getExistingDirectory(None, title, ""))


def _open_file(pya: Any, title: str, filter_text: str) -> str:
    dialog = getattr(pya, "QFileDialog", None)
    if dialog is None or not hasattr(dialog, "getOpenFileName"):
        return ""
    return _first_path(dialog.getOpenFileName(None, title, "", filter_text))


def _save_file(pya: Any, title: str, filter_text: str) -> str:
    dialog = getattr(pya, "QFileDialog", None)
    if dialog is None or not hasattr(dialog, "getSaveFileName"):
        return ""
    return _first_path(dialog.getSaveFileName(None, title, "session.json", filter_text))


def _mode_choice(pya: Any, registry: ModeRegistry) -> SessionMode | SessionModeId:
    values = registry.visible_mode_ids()
    chosen = _item_choice(pya, "Choose Session Mode", values)
    if not chosen:
        return SessionMode.SIMPLE_CAPTURE
    try:
        return SessionMode(chosen)
    except ValueError:
        return SessionModeId(chosen) if chosen in values else SessionMode.SIMPLE_CAPTURE


def _item_choice(pya: Any, title: str, values: tuple[str, ...]) -> str:
    dialog = getattr(pya, "QInputDialog", None)
    if dialog is None or not hasattr(dialog, "getItem"):
        return values[0] if values else ""
    result = dialog.getItem(None, title, title, values, 0, False)
    chosen = _accepted_item(result)
    if not chosen:
        return ""
    return chosen if chosen in values else (values[0] if values else "")


def _accepted_item(result: Any) -> str:
    if isinstance(result, tuple):
        if len(result) >= 2 and not result[1]:
            return ""
        return str(result[0]) if result else ""
    return str(result) if result else ""


def _first_path(result: Any) -> str:
    if isinstance(result, tuple):
        return str(result[0]) if result and result[0] else ""
    return str(result) if result else ""
