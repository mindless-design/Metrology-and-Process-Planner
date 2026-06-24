"""Application controller for opening the unified session editor."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any, Optional, Union

from metrology_process_planner.persistence.paths import SessionPaths
from metrology_process_planner.ui.session_editor import (
    InMemorySessionEditorWidgetFactory,
    SessionEditorCallbacks,
    SessionEditorShell,
)
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
    ) -> None:
        self._store = document_store if document_store is not None else SessionDocumentStore()
        self._shell = shell if shell is not None else _default_shell()
        self._adapter = adapter if adapter is not None else DefaultSessionModeAdapter()
        self.current_document: Optional[SessionDocument] = None
        self.last_action_result: Optional[EditorActionResult] = None
        self.current_window: Optional[Any] = None
        self._callbacks: Optional[SessionEditorCallbacks] = None

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
        self.current_document = document

        def on_select(item_id: str) -> None:
            action = EditorAction(EditorActionType.SELECT_ITEM, "Select", item_id)
            self._dispatch(dispatcher, action)

        def on_action(action: EditorAction) -> None:
            self._dispatch(dispatcher, action)

        callbacks = SessionEditorCallbacks(on_select_item=on_select, on_action=on_action)
        self._callbacks = callbacks
        window = self._shell.open(document, self._adapter, callbacks)
        self.current_window = window
        return SessionEditorOpenResult("opened", document=document, window=window)

    def open_current_session(self) -> SessionEditorOpenResult:
        """Resolve the editor command when no active session provider exists yet."""

        if self.current_document is None:
            return SessionEditorOpenResult("unavailable", "No active session is loaded.")
        return self.open_document(self.current_document)

    def _dispatch(self, dispatcher: EditorActionDispatcher, action: EditorAction) -> None:
        if self.current_document is None:
            return
        result = dispatcher.dispatch(self.current_document, action)
        self.current_document = result.document
        self.last_action_result = result
        if self.current_window is not None and self._callbacks is not None:
            self._shell.render(
                self.current_window,
                self.current_document,
                self._adapter,
                self._callbacks,
            )


def _default_shell() -> SessionEditorShell:
    return SessionEditorShell(InMemorySessionEditorWidgetFactory())


def _paths_for(path_or_folder: PathInput) -> SessionPaths:
    path = Path(path_or_folder)
    folder = path if path.is_dir() else path.parent
    return SessionPaths.for_folder(folder)
