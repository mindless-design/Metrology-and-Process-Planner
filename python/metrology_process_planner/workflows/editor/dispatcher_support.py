"""Shared helpers for editor action dispatch."""

from __future__ import annotations

from typing import Protocol

from metrology_process_planner.domains.session import SessionRecord
from metrology_process_planner.workflows.canvas_interaction_models import InteractionContext
from metrology_process_planner.workflows.editor.builder import SessionDocumentBuilder
from metrology_process_planner.workflows.editor.document import SessionDocument
from metrology_process_planner.workflows.editor.editing import select_canvas_object, select_item
from metrology_process_planner.workflows.editor.view_models import EditorAction


class _DocumentBuilderOwner(Protocol):
    """Dispatcher capability needed to rebuild editor documents."""

    _builder: SessionDocumentBuilder


def _empty_context() -> InteractionContext:
    return InteractionContext()


def _record_id(document: SessionDocument, item_id: str) -> str:
    item = document.items_by_id[item_id]
    if item.record_ref is None:
        return ""
    return item.record_ref.record_id


def _payload_value(action: EditorAction, key: str) -> str:
    values = dict(action.payload)
    return values.get(key, "")


def _rebuild_document(
    dispatcher: _DocumentBuilderOwner,
    session: SessionRecord,
    document: SessionDocument,
) -> SessionDocument:
    rebuilt = dispatcher._builder.build(session, raw_payload=document.raw_payload)
    return _preserve_selection(rebuilt, document)


def _with_session(
    dispatcher: _DocumentBuilderOwner,
    document: SessionDocument,
    session: SessionRecord,
) -> SessionDocument:
    return _preserve_selection(
        dispatcher._builder.build(session, raw_payload=document.raw_payload),
        document,
    )


def _preserve_selection(
    rebuilt: SessionDocument,
    previous: SessionDocument,
) -> SessionDocument:
    selected_item_id = previous.selection.selected_item_id
    if selected_item_id in rebuilt.items_by_id:
        return select_item(rebuilt, selected_item_id)
    for canvas_object_id in previous.selection.selected_canvas_object_ids:
        selected = select_canvas_object(rebuilt, canvas_object_id)
        if selected.selection.selected_item_id != rebuilt.selection.selected_item_id:
            return selected
    return rebuilt
