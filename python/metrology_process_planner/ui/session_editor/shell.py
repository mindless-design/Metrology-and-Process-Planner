"""Minimal generic session editor shell with injectable widget backend."""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
from typing import Any, Protocol

from metrology_process_planner.workflows.editor.adapters import SessionModeAdapter
from metrology_process_planner.workflows.editor.document import SessionDocument
from metrology_process_planner.workflows.editor.view_models import EditorAction

SelectionCallback = Callable[[str], None]
ActionCallback = Callable[[EditorAction], None]
NavigatorRows = tuple[tuple[str, tuple[tuple[str, str], ...]], ...]
PreviewRows = tuple[tuple[str, str, str], ...]


@dataclass(frozen=True)
class SessionEditorCallbacks:
    """Callbacks emitted by the editor shell for selection and actions."""

    on_select_item: SelectionCallback
    on_action: ActionCallback


class SessionEditorWidgetFactory(Protocol):
    """Backend contract for constructing the editor shell widgets."""

    def create_window(self, title: str) -> Any:
        """Create a top-level editor window."""

    def set_header(self, window: Any, entries: tuple[tuple[str, str], ...]) -> None:
        """Render the compact header/session bar."""

    def set_navigator(
        self,
        window: Any,
        groups: NavigatorRows,
        selected_item_id: str,
        on_select: SelectionCallback,
    ) -> None:
        """Render the left session navigator."""

    def set_preview(self, window: Any, previews: PreviewRows) -> None:
        """Render the center preview/details area."""

    def set_inspector(
        self,
        window: Any,
        fields: tuple[tuple[str, str, str], ...],
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
        self._factory.set_header(window, _header_entries(document))
        self._factory.set_navigator(
            window,
            _navigator_groups(document),
            document.selection.selected_item_id,
            callbacks.on_select_item,
        )
        self._factory.set_preview(window, _preview_rows(document, adapter))
        self._factory.set_inspector(
            window,
            _metadata_rows(document, adapter),
            adapter.actions(document.session, selected),
            callbacks.on_action,
        )
        self._factory.set_status(window, _status_text(document))


class InMemorySessionEditorWidgetFactory:
    """Widget factory used by tests and non-GUI smoke checks."""

    def create_window(self, title: str) -> dict[str, Any]:
        """Create an in-memory window record."""

        return {"title": title, "shown": False}

    def set_header(self, window: dict[str, Any], entries: tuple[tuple[str, str], ...]) -> None:
        """Store rendered header entries."""

        window["header"] = entries

    def set_navigator(
        self,
        window: dict[str, Any],
        groups: NavigatorRows,
        selected_item_id: str,
        on_select: SelectionCallback,
    ) -> None:
        """Store rendered navigator groups and callback."""

        window["navigator"] = groups
        window["selected_item_id"] = selected_item_id
        window["on_select"] = on_select

    def set_preview(self, window: dict[str, Any], previews: PreviewRows) -> None:
        """Store rendered preview rows."""

        window["preview"] = previews

    def set_inspector(
        self,
        window: dict[str, Any],
        fields: tuple[tuple[str, str, str], ...],
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


def _header_entries(document: SessionDocument) -> tuple[tuple[str, str], ...]:
    dirty = "Unsaved" if document.dirty_state.is_dirty else "Saved"
    return (
        ("Session", document.session.name),
        ("Mode", document.session.mode.value),
        ("Dirty", dirty),
        ("Warnings", str(len(document.warning_view_models))),
    )


def _navigator_groups(document: SessionDocument) -> NavigatorRows:
    rows = []
    for group in document.navigator_groups:
        items = tuple((item_id, document.items_by_id[item_id].label) for item_id in group.item_ids)
        rows.append((group.label, items))
    return tuple(rows)


def _preview_rows(
    document: SessionDocument,
    adapter: SessionModeAdapter,
) -> PreviewRows:
    item = document.items_by_id[document.selection.selected_item_id]
    return tuple(
        (preview.role, preview.label, preview.artifact_path or preview.placeholder)
        for preview in adapter.preview_options(document.session, item)
    )


def _metadata_rows(
    document: SessionDocument,
    adapter: SessionModeAdapter,
) -> tuple[tuple[str, str, str], ...]:
    item = document.items_by_id[document.selection.selected_item_id]
    return tuple(
        (field.key, field.label, field.value)
        for field in adapter.metadata_fields(document.session, item)
    )


def _status_text(document: SessionDocument) -> str:
    if document.warning_view_models:
        return f"{len(document.warning_view_models)} warning(s)"
    return "Ready"
