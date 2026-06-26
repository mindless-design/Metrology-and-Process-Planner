"""Recent session path registry for the editor store."""

from __future__ import annotations

from pathlib import Path

from metrology_process_planner.workflows.editor.store_io import PathInput, resolve_session_json


class RecentSessionRegistry:
    """Bounded recent-session list for user-openable session JSON files."""

    def __init__(self, limit: int = 10) -> None:
        self._limit = limit
        self._paths: tuple[Path, ...] = ()

    def add(self, path_or_folder: PathInput) -> None:
        """Add a session path to the front of the recent list."""

        path = resolve_session_json(path_or_folder).resolve()
        remaining = tuple(item for item in self._paths if item != path)
        self._paths = (path, *remaining)[: self._limit]

    def list(self) -> tuple[Path, ...]:
        """Return known recent session JSON paths."""

        return self._paths
