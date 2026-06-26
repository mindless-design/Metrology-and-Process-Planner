"""Session editor persistence and lifecycle controller methods."""

from __future__ import annotations

from pathlib import Path
from typing import Any, cast

from metrology_process_planner.app.active_session import ActiveSessionContext
from metrology_process_planner.app.session_editor_models import (
    PathInput,
    SessionEditorOpenResult,
)
from metrology_process_planner.app.window_registry import WindowOpenStatus
from metrology_process_planner.persistence.paths import SessionPaths
from metrology_process_planner.workflows.editor.store import NewSessionRequest


class SessionEditorLifecycleMixin:
    """Open, save, recent-list, and close flows for the session editor."""

    current_document: Any
    current_paths: SessionPaths | None
    current_window: Any

    def open_session_path(self: Any, path_or_folder: PathInput) -> SessionEditorOpenResult:
        """Open a session JSON file or folder in the unified editor shell."""

        document = self._session_store.open_session(path_or_folder)
        self._recent_sessions.add(path_or_folder)
        return cast(
            SessionEditorOpenResult,
            self.open_document(document, _paths_for(path_or_folder)),
        )

    def new_session(self: Any, request: NewSessionRequest) -> SessionEditorOpenResult:
        """Create session.json immediately, then open it in the editor."""

        document = self._session_store.new_session(request)
        self._recent_sessions.add(document.loaded_path or request.output_folder)
        return cast(
            SessionEditorOpenResult,
            self.open_document(document, SessionPaths.for_folder(request.output_folder)),
        )

    def save_current_session(self: Any) -> SessionEditorOpenResult:
        """Save the active session document to its loaded path."""

        if self.current_document is None or self.current_paths is None:
            return SessionEditorOpenResult("unavailable", "No active session is loaded.")
        saved = self._session_store.save(self.current_document, self.current_paths)
        self.current_document = saved
        self.active_context = ActiveSessionContext.from_document(saved)
        self._render_current()
        return SessionEditorOpenResult("saved", document=saved, window=self.current_window)

    def save_current_session_as(
        self: Any,
        destination: PathInput,
    ) -> SessionEditorOpenResult:
        """Save the active document to a new session folder or session.json path."""

        if self.current_document is None:
            return SessionEditorOpenResult("unavailable", "No active session is loaded.")
        saved = self._session_store.save_as(self.current_document, destination)
        self._recent_sessions.add(saved.loaded_path or destination)
        return cast(
            SessionEditorOpenResult,
            self.open_document(saved, _paths_for(saved.loaded_path or destination)),
        )

    def recent_session_paths(self: Any) -> tuple[Path, ...]:
        """Return recent session JSON paths."""

        return cast(tuple[Path, ...], self._recent_sessions.list())

    def close_current_session(
        self: Any,
        disposition: str = "cancel",
    ) -> SessionEditorOpenResult:
        """Close the active session if edits are saved, discarded, or cancelled."""

        if self.current_document is None:
            return SessionEditorOpenResult("closed", "No active session is loaded.")
        if self.current_document.dirty_state.is_dirty:
            if disposition == "save":
                saved = cast(SessionEditorOpenResult, self.save_current_session())
                if saved.status not in {"saved", "success"}:
                    return saved
            elif disposition != "discard":
                return SessionEditorOpenResult(
                    "blocked",
                    "Session has unsaved changes; choose save, discard, or cancel.",
                    document=self.current_document,
                    window=self.current_window,
                )
        session_id = self.current_document.session.id
        self._window_registry.close(f"session-editor:{session_id}")
        self.current_document = None
        self.current_paths = None
        self.current_window = None
        self.active_context = ActiveSessionContext()
        return SessionEditorOpenResult("closed", "Session closed.")

    def open_start_screen(self: Any) -> SessionEditorOpenResult:
        """Open the no-active-session start state for explicit document actions."""

        registry_result = self._window_registry.open_or_raise(
            "session-editor:start",
            "Session Editor",
            _start_screen_window,
            refresh_existing=_refresh_start_screen,
        )
        if registry_result.status is WindowOpenStatus.FAILED:
            return SessionEditorOpenResult("failed", registry_result.message)
        self.current_window = registry_result.window
        return SessionEditorOpenResult(
            "start_screen",
            "No active Process Planner session.",
            window=registry_result.window,
        )


def _paths_for(path_or_folder: PathInput) -> SessionPaths:
    path = Path(path_or_folder)
    return SessionPaths.for_folder(path if path.is_dir() else path.parent)


def _start_screen_window() -> dict[str, Any]:
    return {
        "title": "Session Editor",
        "start_screen": True,
        "message": "No active Process Planner session.",
        "actions": ("New Session", "Open Existing Session JSON", "Open Recent"),
        "shown": True,
    }


def _refresh_start_screen(window: Any) -> None:
    if isinstance(window, dict):
        window.update(_start_screen_window())
