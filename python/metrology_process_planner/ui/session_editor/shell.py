"""Minimal generic session editor shell with injectable widget backend."""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
from typing import Any, Protocol

from metrology_process_planner.ui.session_editor.header import (
    header_entries,
    primary_actions,
    status_text,
)
from metrology_process_planner.ui.session_editor.navigator import (
    NavigatorFilterCallback,
    NavigatorFilterState,
    NavigatorRows,
    navigator_groups,
)
from metrology_process_planner.ui.session_editor.sections import (
    MetadataRows,
    PreviewRows,
    metadata_rows,
    preview_rows,
)
from metrology_process_planner.workflows.editor.adapters import SessionModeAdapter
from metrology_process_planner.workflows.editor.document import SessionDocument
from metrology_process_planner.workflows.editor.view_models import EditorAction

SelectionCallback = Callable[[str], None]
ActionCallback = Callable[[EditorAction], None]


@dataclass(frozen=True)
class SessionEditorCallbacks:
    """Callbacks emitted by the editor shell for selection and actions."""

    on_select_item: SelectionCallback
    on_action: ActionCallback
    on_filter_navigator: NavigatorFilterCallback | None = None
    navigator_filter: NavigatorFilterState = NavigatorFilterState()


class SessionEditorWidgetFactory(Protocol):
    """Backend contract for constructing the editor shell widgets."""

    def create_window(self, title: str) -> Any:
        """Create a top-level editor window."""

    def set_header(self, window: Any, entries: tuple[tuple[str, str], ...]) -> None:
        """Render the compact header/session bar."""

    def set_primary_actions(
        self,
        window: Any,
        actions: tuple[EditorAction, ...],
        on_action: ActionCallback,
    ) -> None:
        """Render the header primary action bar."""

    def set_navigator(
        self,
        window: Any,
        groups: NavigatorRows,
        selected_item_id: str,
        on_select: SelectionCallback,
        on_filter: NavigatorFilterCallback | None,
        filter_state: NavigatorFilterState,
    ) -> None:
        """Render the left session navigator."""

    def set_preview(self, window: Any, previews: PreviewRows) -> None:
        """Render the center preview/details area."""

    def set_inspector(
        self,
        window: Any,
        fields: MetadataRows,
        actions: tuple[EditorAction, ...],
        on_action: ActionCallback,
    ) -> None:
        """Render the right inspector/actions area."""

    def set_status(self, window: Any, text: str) -> None:
        """Render the bottom status/warning strip."""

    def show(self, window: Any) -> None:
        """Show the editor window."""


class SessionEditorShell:
    """Render a generic session editor document using an injected widget backend."""

    def __init__(self, factory: SessionEditorWidgetFactory) -> None:
        self._factory = factory

    def open(
        self,
        document: SessionDocument,
        adapter: SessionModeAdapter,
        callbacks: SessionEditorCallbacks,
    ) -> Any:
        """Build and show the editor shell for one document."""

        window = self._factory.create_window(f"Session Editor - {document.session.name}")
        self.render(window, document, adapter, callbacks)
        self._factory.show(window)
        return window

    def render(
        self,
        window: Any,
        document: SessionDocument,
        adapter: SessionModeAdapter,
        callbacks: SessionEditorCallbacks,
    ) -> None:
        """Render a document into an existing editor shell window."""

        selected = document.items_by_id[document.selection.selected_item_id]
        self._factory.set_header(window, header_entries(document))
        self._factory.set_primary_actions(window, primary_actions(document), callbacks.on_action)
        self._factory.set_navigator(
            window,
            navigator_groups(document, callbacks.navigator_filter),
            document.selection.selected_item_id,
            callbacks.on_select_item,
            callbacks.on_filter_navigator,
            callbacks.navigator_filter,
        )
        self._factory.set_preview(window, preview_rows(document, adapter))
        self._factory.set_inspector(
            window,
            metadata_rows(document, adapter),
            adapter.actions(document.session, selected),
            callbacks.on_action,
        )
        self._factory.set_status(window, status_text(document))


class InMemorySessionEditorWidgetFactory:
    """Widget factory used by tests and non-GUI smoke checks."""

    def create_window(self, title: str) -> dict[str, Any]:
        """Create an in-memory window record."""

        return {"title": title, "shown": False}

    def set_header(self, window: dict[str, Any], entries: tuple[tuple[str, str], ...]) -> None:
        """Store rendered header entries."""

        window["header"] = entries

    def set_primary_actions(
        self,
        window: dict[str, Any],
        actions: tuple[EditorAction, ...],
        on_action: ActionCallback,
    ) -> None:
        """Store rendered primary header actions and callback."""

        window["primary_actions"] = actions
        window["on_primary_action"] = on_action

    def set_navigator(
        self,
        window: dict[str, Any],
        groups: NavigatorRows,
        selected_item_id: str,
        on_select: SelectionCallback,
        on_filter: NavigatorFilterCallback | None,
        filter_state: NavigatorFilterState,
    ) -> None:
        """Store rendered navigator groups and callback."""

        window["navigator"] = groups
        window["selected_item_id"] = selected_item_id
        window["on_select"] = on_select
        window["navigator_filter"] = filter_state
        window["on_filter_navigator"] = on_filter

    def set_preview(self, window: dict[str, Any], previews: PreviewRows) -> None:
        """Store rendered preview rows."""

        window["preview"] = previews

    def set_inspector(
        self,
        window: dict[str, Any],
        fields: MetadataRows,
        actions: tuple[EditorAction, ...],
        on_action: ActionCallback,
    ) -> None:
        """Store rendered inspector fields, actions, and callback."""

        window["fields"] = fields
        window["actions"] = actions
        window["on_action"] = on_action

    def set_status(self, window: dict[str, Any], text: str) -> None:
        """Store rendered status text."""

        window["status"] = text

    def show(self, window: dict[str, Any]) -> None:
        """Mark the in-memory window as shown."""

        window["shown"] = True
