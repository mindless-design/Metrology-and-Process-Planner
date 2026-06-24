"""Application controller for opening the unified session editor."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any, Optional, Union

from metrology_process_planner.app.session_editor_command_map import command_for_action
from metrology_process_planner.app.window_registry import (
    WindowOpenStatus,
    WindowRegistry,
)
from metrology_process_planner.persistence.paths import SessionPaths
from metrology_process_planner.ui.session_editor import (
    InMemorySessionEditorWidgetFactory,
    NavigatorFilterState,
    SessionEditorCallbacks,
    SessionEditorShell,
)
from metrology_process_planner.ui.shell import CommandRouter, CommandRouteResult
from metrology_process_planner.workflows.editor.adapters import DefaultSessionModeAdapter
from metrology_process_planner.workflows.editor.dispatcher import EditorActionDispatcher
from metrology_process_planner.workflows.editor.dispatcher_results import EditorActionResult
from metrology_process_planner.workflows.editor.document import SessionDocument
from metrology_process_planner.workflows.editor.store import SessionDocumentStore
from metrology_process_planner.workflows.editor.view_models import EditorAction, EditorActionType

PathInput = Union[str, Path]


@dataclass(frozen=True)
class SessionEditorOpenResult:
    """Result of opening or resolving the unified session editor."""

    status: str
    message: str = ""
    document: Optional[SessionDocument] = None
    window: Optional[Any] = None


class SessionEditorController:
    """Build editor documents, shells, and action dispatch callbacks."""

    def __init__(
        self,
        document_store: Optional[SessionDocumentStore] = None,
        shell: Optional[SessionEditorShell] = None,
        adapter: Optional[DefaultSessionModeAdapter] = None,
        window_registry: Optional[WindowRegistry[Any]] = None,
    ) -> None:
        self._store = document_store if document_store is not None else SessionDocumentStore()
        self._shell = shell if shell is not None else _default_shell()
        self._adapter = adapter if adapter is not None else DefaultSessionModeAdapter()
        self._window_registry = (
            window_registry if window_registry is not None else WindowRegistry()
        )
        self.current_document: Optional[SessionDocument] = None
        self.last_action_result: Optional[EditorActionResult] = None
        self.last_command_result: Optional[CommandRouteResult] = None
        self.current_window: Optional[Any] = None
        self._callbacks: Optional[SessionEditorCallbacks] = None
        self._command_router: Optional[CommandRouter] = None
        self._dispatcher: Optional[EditorActionDispatcher] = None
        self._routed_action: Optional[EditorAction] = None
        self._navigator_filter = NavigatorFilterState()

    def set_command_router(self, command_router: Optional[CommandRouter]) -> None:
        """Set the app command router used for editor window/lifecycle intents."""

        self._command_router = command_router

    def open_session_path(self, path_or_folder: PathInput) -> SessionEditorOpenResult:
        """Open a session JSON file or folder in the unified editor shell."""

        document = self._store.load(path_or_folder)
        return self.open_document(document, _paths_for(path_or_folder))

    def open_document(
        self,
        document: SessionDocument,
        paths: Optional[SessionPaths] = None,
    ) -> SessionEditorOpenResult:
        """Open an already-built document in the unified editor shell."""

        dispatcher = EditorActionDispatcher(paths=paths)
        self._dispatcher = dispatcher
        self.current_document = document
        callbacks = _callbacks_for(self, self._navigator_filter)
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
            return SessionEditorOpenResult("unavailable", "No active session is loaded.")
        return self.open_document(self.current_document)

    def dispatch_current_action(
        self,
        action: EditorAction,
        *,
        allow_app_route: bool = True,
    ) -> Optional[EditorActionResult]:
        """Dispatch an editor action against the active document and rerender."""

        if self.current_document is None:
            return None
        if allow_app_route and self._route_app_command(action):
            return self.last_action_result
        dispatcher = self._dispatcher if self._dispatcher is not None else EditorActionDispatcher()
        result = dispatcher.dispatch(self.current_document, action)
        self.current_document = result.document
        self.last_action_result = result
        self._render_current()
        return result

    def replace_current_document(self, document: SessionDocument) -> None:
        """Replace the active document after an app-owned command update."""

        self.current_document = document
        self._render_current()

    def filter_navigator(self, query: str, warning_filter: str = "all") -> None:
        """Update transient navigator filter state and rerender."""

        self._navigator_filter = NavigatorFilterState(query, warning_filter)
        if self._callbacks is not None:
            self._callbacks = _callbacks_for(self, self._navigator_filter)
        self._render_current()

    @property
    def routed_action(self) -> Optional[EditorAction]:
        """Return the editor action currently being routed through app commands."""

        return self._routed_action

    def _route_app_command(self, action: EditorAction) -> bool:
        command_id = command_for_action(action)
        if command_id is None or self._command_router is None:
            return False
        self._routed_action = action
        try:
            self.last_command_result = self._command_router.route(command_id)
        finally:
            self._routed_action = None
        if self.current_document is None:
            return True
        self._render_current()
        return True

    def _render_current(self) -> None:
        _render_current(self)


def _default_shell() -> SessionEditorShell:
    return SessionEditorShell(InMemorySessionEditorWidgetFactory())


def _callbacks_for(
    controller: SessionEditorController,
    filter_state: NavigatorFilterState,
) -> SessionEditorCallbacks:
    def on_select(item_id: str) -> None:
        controller.dispatch_current_action(
            EditorAction(EditorActionType.SELECT_ITEM, "Select", item_id)
        )

    def on_action(action: EditorAction) -> None:
        controller.dispatch_current_action(action)

    return SessionEditorCallbacks(
        on_select,
        on_action,
        controller.filter_navigator,
        filter_state,
    )


def _render_current(controller: SessionEditorController) -> None:
    if (
        controller.current_document is not None
        and controller.current_window is not None
        and controller._callbacks is not None
    ):
        controller._shell.render(
            controller.current_window,
            controller.current_document,
            controller._adapter,
            controller._callbacks,
        )


def _paths_for(path_or_folder: PathInput) -> SessionPaths:
    path = Path(path_or_folder)
    return SessionPaths.for_folder(path if path.is_dir() else path.parent)
