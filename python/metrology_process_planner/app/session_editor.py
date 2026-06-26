"""Application controller for opening the unified session editor."""

from __future__ import annotations

from typing import Any, Optional

from metrology_process_planner.app.active_session import ActiveSessionContext
from metrology_process_planner.app.session_editor_lifecycle import SessionEditorLifecycleMixin
from metrology_process_planner.app.session_editor_models import SessionEditorOpenResult
from metrology_process_planner.app.session_editor_routing import SessionEditorRoutingMixin
from metrology_process_planner.app.session_editor_surface import (
    callbacks_for,
    default_shell,
    render_current,
)
from metrology_process_planner.app.window_registry import (
    WindowOpenStatus,
    WindowRegistry,
)
from metrology_process_planner.domains.session import ModeRegistry
from metrology_process_planner.persistence.paths import SessionPaths
from metrology_process_planner.ui.session_editor import (
    NavigatorFilterState,
    SessionEditorCallbacks,
    SessionEditorShell,
)
from metrology_process_planner.ui.shell import CommandRouter, CommandRouteResult
from metrology_process_planner.workflows.editor.adapters import DefaultSessionModeAdapter
from metrology_process_planner.workflows.editor.dispatcher import EditorActionDispatcher
from metrology_process_planner.workflows.editor.dispatcher_results import EditorActionResult
from metrology_process_planner.workflows.editor.document import SessionDocument
from metrology_process_planner.workflows.editor.store import (
    RecentSessionRegistry,
    SessionDocumentStore,
    SessionStore,
)
from metrology_process_planner.workflows.editor.view_models import EditorAction


class SessionEditorController(SessionEditorRoutingMixin, SessionEditorLifecycleMixin):
    """Build editor documents, shells, and action dispatch callbacks."""

    def __init__(
        self,
        document_store: Optional[SessionDocumentStore] = None,
        shell: Optional[SessionEditorShell] = None,
        adapter: Optional[DefaultSessionModeAdapter] = None,
        window_registry: Optional[WindowRegistry[Any]] = None,
        session_store: Optional[SessionStore] = None,
        recent_sessions: Optional[RecentSessionRegistry] = None,
        mode_registry: ModeRegistry | None = None,
    ) -> None:
        self._store = (
            document_store
            if document_store is not None
            else SessionDocumentStore(mode_registry=mode_registry)
        )
        self._session_store = session_store if session_store is not None else SessionStore(
            self._store,
            mode_registry=mode_registry,
        )
        self._recent_sessions = (
            recent_sessions if recent_sessions is not None else RecentSessionRegistry()
        )
        self._shell = shell if shell is not None else default_shell()
        self._adapter = (
            adapter if adapter is not None else DefaultSessionModeAdapter(mode_registry)
        )
        self._window_registry = (
            window_registry if window_registry is not None else WindowRegistry()
        )
        self.current_document: Optional[SessionDocument] = None
        self.current_paths: Optional[SessionPaths] = None
        self.active_context = ActiveSessionContext()
        self.last_action_result: Optional[EditorActionResult] = None
        self.last_command_result: Optional[CommandRouteResult] = None
        self.current_window: Optional[Any] = None
        self._callbacks: Optional[SessionEditorCallbacks] = None
        self._command_router: Optional[CommandRouter] = None
        self._dispatcher: Optional[EditorActionDispatcher] = None
        self._routed_action: Optional[EditorAction] = None
        self._mode_registry = mode_registry
        self._navigator_filter = NavigatorFilterState()

    def set_command_router(self, command_router: Optional[CommandRouter]) -> None:
        """Set the app command router used for editor window/lifecycle intents."""

        self._command_router = command_router

    @property
    def mode_registry(self) -> ModeRegistry | None:
        """Return the loaded mode registry used by this editor controller."""

        return self._mode_registry

    def open_document(
        self,
        document: SessionDocument,
        paths: Optional[SessionPaths] = None,
    ) -> SessionEditorOpenResult:
        """Open an already-built document in the unified editor shell."""

        dispatcher = EditorActionDispatcher(paths=paths, mode_registry=self._mode_registry)
        self._dispatcher = dispatcher
        self.current_document = document
        self.current_paths = paths
        self.active_context = ActiveSessionContext.from_document(document)
        callbacks = callbacks_for(self, self._navigator_filter)
        self._callbacks = callbacks
        registry_result = self._window_registry.get_or_create_session_editor(
            document.session.id,
            f"Session Editor - {document.session.name}",
            lambda: self._shell.open(document, self._adapter, callbacks),
            refresh_existing=lambda window: self._shell.render(
                window,
                document,
                self._adapter,
                callbacks,
            ),
        )
        if registry_result.status is WindowOpenStatus.FAILED:
            return SessionEditorOpenResult("failed", registry_result.message, document=document)
        window = registry_result.window
        self.current_window = window
        status = "raised" if registry_result.status is WindowOpenStatus.RAISED else "opened"
        return SessionEditorOpenResult(status, document=document, window=window)

    def open_current_session(self) -> SessionEditorOpenResult:
        """Resolve the editor command when no active session provider exists yet."""

        if self.current_document is None:
            return self.open_start_screen()
        return self.open_document(self.current_document)

    def open_start_screen(self) -> SessionEditorOpenResult:
        """Open the no-active-session start state for explicit document actions."""

        return super().open_start_screen()

    def filter_navigator(self, query: str, warning_filter: str = "all") -> None:
        """Update transient navigator filter state and rerender."""

        self._navigator_filter = NavigatorFilterState(query, warning_filter)
        if self._callbacks is not None:
            self._callbacks = callbacks_for(self, self._navigator_filter)
        self._render_current()

    def _render_current(self) -> None:
        render_current(self)
