"""Application controller for opening the unified session editor."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any, Optional, Union

from metrology_process_planner.app.commands import CommandId
from metrology_process_planner.app.window_registry import (
    WindowOpenStatus,
    WindowRegistry,
)
from metrology_process_planner.persistence.paths import SessionPaths
from metrology_process_planner.ui.session_editor import (
    InMemorySessionEditorWidgetFactory,
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

        def on_select(item_id: str) -> None:
            action = EditorAction(EditorActionType.SELECT_ITEM, "Select", item_id)
            self.dispatch_current_action(action)

        def on_action(action: EditorAction) -> None:
            self.dispatch_current_action(action)

        callbacks = SessionEditorCallbacks(on_select_item=on_select, on_action=on_action)
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

    @property
    def routed_action(self) -> Optional[EditorAction]:
        """Return the editor action currently being routed through app commands."""

        return self._routed_action

    def _route_app_command(self, action: EditorAction) -> bool:
        command_id = _command_for_action(action)
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
        if (
            self.current_document is not None
            and self.current_window is not None
            and self._callbacks is not None
        ):
            self._shell.render(
                self.current_window,
                self.current_document,
                self._adapter,
                self._callbacks,
            )


def _default_shell() -> SessionEditorShell:
    return SessionEditorShell(InMemorySessionEditorWidgetFactory())


def _command_for_action(action: EditorAction) -> Optional[CommandId]:
    return _EDITOR_COMMANDS.get(action.action_type)


_EDITOR_COMMANDS: dict[EditorActionType, CommandId] = {
    EditorActionType.ADD_MEASUREMENT: CommandId.ADD_MEASUREMENT,
    EditorActionType.ATTACH_RECIPE: CommandId.ATTACH_RECIPE,
    EditorActionType.COMPOSITE_DISCARD: CommandId.DISCARD_PENDING_CAPTURE,
    EditorActionType.COMPOSITE_RETAKE_INNER: CommandId.RETAKE_INNER_FEATURE,
    EditorActionType.COMPOSITE_RETAKE_PARENT: CommandId.RETAKE_PARENT_CAPTURE,
    EditorActionType.COMPOSITE_SAVE: CommandId.SAVE_COMPOSITE_CAPTURE,
    EditorActionType.DETACH_RECIPE: CommandId.DETACH_RECIPE,
    EditorActionType.DISCARD_MEASUREMENT: CommandId.DISCARD_MEASUREMENT,
    EditorActionType.EXIT_SESSION: CommandId.END_ACTIVE_SESSION,
    EditorActionType.EXPORT_CSV: CommandId.EXPORT_CSV,
    EditorActionType.OPEN_OUTPUT_FOLDER: CommandId.OPEN_OUTPUT_FOLDER,
    EditorActionType.PENDING_DISCARD: CommandId.DISCARD_PENDING_CAPTURE,
    EditorActionType.PENDING_RETAKE: CommandId.RETAKE_PENDING_CAPTURE,
    EditorActionType.PENDING_SAVE: CommandId.SAVE_PENDING_CAPTURE,
    EditorActionType.REGENERATE_ARTIFACT: CommandId.REGENERATE_ARTIFACT,
    EditorActionType.REGENERATE_PROCESS_OUTPUT: CommandId.REGENERATE_PROCESS_OUTPUT,
    EditorActionType.REOPEN_SETUP: CommandId.OPEN_SETUP_GUIDE,
    EditorActionType.RETAKE_MEASUREMENT_LINE: CommandId.RETAKE_MEASUREMENT_LINE,
    EditorActionType.SAVE_EDITS: CommandId.SAVE_SESSION_EDITS,
    EditorActionType.SAVE_MEASUREMENT: CommandId.SAVE_MEASUREMENT,
    EditorActionType.VALIDATE_PROCESS_CONTEXT: CommandId.VALIDATE_PROCESS_CONTEXT,
}


def _paths_for(path_or_folder: PathInput) -> SessionPaths:
    path = Path(path_or_folder)
    return SessionPaths.for_folder(path if path.is_dir() else path.parent)
