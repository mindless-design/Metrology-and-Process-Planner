"""Modeless active-session lifecycle command handlers."""

from __future__ import annotations

from metrology_process_planner.app.capture_commands import CaptureCommandService
from metrology_process_planner.app.command_types import CommandBlockedError
from metrology_process_planner.app.diagnostics import AdvancedDiagnosticsController
from metrology_process_planner.app.session_editor import SessionEditorController
from metrology_process_planner.app.setup_guide import SetupGuideController
from metrology_process_planner.app.window_registry import WindowRegistry
from metrology_process_planner.workflows import InteractionContext


class SessionLifecycleService:
    """Apply active-session lifecycle commands without blocking dialogs."""

    def __init__(
        self,
        session_editor: SessionEditorController,
        setup_guide: SetupGuideController,
        diagnostics: AdvancedDiagnosticsController,
        capture_commands: CaptureCommandService,
        window_registry: WindowRegistry[object],
    ) -> None:
        self._session_editor = session_editor
        self._setup_guide = setup_guide
        self._diagnostics = diagnostics
        self._capture_commands = capture_commands
        self._window_registry = window_registry

    def end_active_session(self) -> None:
        """Close safe modeless session surfaces and clear active state."""

        self._block_if_pending_or_dirty()
        session_id = self._active_session_id()
        self._capture_commands.context = InteractionContext()
        self._close_session_editor(session_id)
        self._close_setup_guide()
        self._close_diagnostics(session_id)

    def _block_if_pending_or_dirty(self) -> None:
        document = self._session_editor.current_document
        if document is not None and document.dirty_state.is_dirty:
            raise CommandBlockedError(
                "Session has unsaved editor edits.",
                "Save or discard unsaved edits before ending the active session.",
            )
        session = document.session if document is not None else self._setup_guide.active_session
        if session is not None and session.pending_captures:
            raise CommandBlockedError(
                "Session has pending capture review items.",
                "Save, retake, discard, or exit pending captures before ending the session.",
            )

    def _active_session_id(self) -> str:
        document = self._session_editor.current_document
        if document is not None:
            return document.session.id
        if self._setup_guide.active_session is not None:
            return self._setup_guide.active_session.id
        if self._diagnostics.active_session is not None:
            return self._diagnostics.active_session.id
        return ""

    def _close_session_editor(self, session_id: str) -> None:
        if session_id:
            self._window_registry.close(f"session-editor:{session_id}")
        self._session_editor.close_current_session("discard")
        self._session_editor.last_action_result = None

    def _close_setup_guide(self) -> None:
        self._setup_guide.close_current()
        self._setup_guide.set_active_session(None)

    def _close_diagnostics(self, session_id: str) -> None:
        if session_id:
            self._window_registry.close(f"advanced-diagnostics:{session_id}")
        self._diagnostics.active_session = None
        self._diagnostics.active_paths = None
