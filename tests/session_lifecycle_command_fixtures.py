"""Fixtures for session lifecycle command adapter tests."""

from __future__ import annotations

from pathlib import Path

from metrology_process_planner.app.session_path_adapter import (
    NewSessionSelection,
    PathSelection,
)
from metrology_process_planner.persistence.paths import SessionPaths
from metrology_process_planner.workflows.editor import SessionDocumentStore


class FakePathAdapter:
    """Fake operator path adapter for command tests."""

    def __init__(
        self,
        new_session: NewSessionSelection | None = None,
        open_session: PathSelection | None = None,
        recent_session: PathSelection | None = None,
        save_as: PathSelection | None = None,
    ) -> None:
        self._new_session = new_session
        self._open_session = open_session
        self._recent_session = recent_session
        self._save_as = save_as

    def select_new_session(self) -> NewSessionSelection:
        """Return the configured new-session selection."""

        return self._new_session or NewSessionSelection()

    def select_open_session(self) -> PathSelection:
        """Return the configured open-session path."""

        return self._open_session or PathSelection()

    def select_recent_session(self, recent_paths: tuple[Path, ...]) -> PathSelection:
        """Return the configured recent-session path."""

        return self._recent_session or PathSelection()

    def select_save_as_destination(self) -> PathSelection:
        """Return the configured save-as destination."""

        return self._save_as or PathSelection()


def document_store() -> SessionDocumentStore:
    """Return a session document store for fixture setup."""

    return SessionDocumentStore()


def paths_for(path: str | Path) -> SessionPaths:
    """Return session paths for a folder."""

    return SessionPaths.for_folder(Path(path))
