"""Pure editing helpers for session editor documents."""

from __future__ import annotations

from dataclasses import replace

from metrology_process_planner.domains.artifacts.artifact_invalidation import (
    invalidate_capture_edit,
    invalidate_measurement_edit,
)
from metrology_process_planner.domains.session import ModeRegistry, SessionRecord
from metrology_process_planner.workflows.editor.document import (
    DirtyState,
    EditorSelectionState,
    SessionDocument,
)
from metrology_process_planner.workflows.editor.editing_apply import (
    apply_capture_edit,
    apply_measurement_edit,
    apply_pending_edit,
)


def select_item(document: SessionDocument, item_id: str) -> SessionDocument:
    """Return a document with one editor item selected."""

    item = document.items_by_id.get(item_id)
    if item is None:
        return document
    return replace(
        document,
        selection=EditorSelectionState(
            selected_item_id=item_id,
            selected_canvas_object_ids=item.canvas_object_ids,
        ),
    )


def select_canvas_object(document: SessionDocument, canvas_object_id: str) -> SessionDocument:
    """Return a document selected by a referenced canvas object id."""

    item_id = (document.canvas_object_to_item_id or {}).get(canvas_object_id)
    if item_id is None:
        return document
    return select_item(document, item_id)


def mark_metadata_edit(
    document: SessionDocument,
    item_id: str,
    field_key: str,
    value: str,
    mode_registry: ModeRegistry | None = None,
) -> SessionDocument:
    """Return a document with one unsaved metadata edit tracked."""

    edits = tuple(
        edit
        for edit in document.dirty_state.unsaved_metadata_edits
        if not (edit[0] == item_id and edit[1] == field_key)
    )
    dirty_items = _append_unique(document.dirty_state.dirty_item_ids, item_id)
    dirty = replace(
        document.dirty_state,
        is_dirty=True,
        dirty_item_ids=dirty_items,
        unsaved_metadata_edits=edits + ((item_id, field_key, value),),
    )
    session = _session_with_edit_invalidation(document, item_id, field_key, mode_registry)
    return replace(document, session=session, dirty_state=dirty)


def mark_pending_dirty(document: SessionDocument) -> SessionDocument:
    """Return a document with pending capture edits marked dirty."""

    dirty = replace(document.dirty_state, is_dirty=True, unsaved_pending_capture=True)
    return replace(document, dirty_state=dirty)


def mark_clean(document: SessionDocument, revision: int) -> SessionDocument:
    """Return a document with dirty state cleared after a successful save."""

    return replace(document, dirty_state=DirtyState(last_saved_revision=revision))


def apply_metadata_edits(
    document: SessionDocument,
    mode_registry: ModeRegistry | None = None,
) -> SessionDocument:
    """Return a document whose canonical session includes tracked metadata edits."""

    session = document.session
    for item_id, field_key, value in document.dirty_state.unsaved_metadata_edits:
        item = document.items_by_id.get(item_id)
        if item_id == "dashboard" and field_key in {"name", "session_name"}:
            session = replace(session, name=value)
        elif item is not None and item.record_ref is not None:
            if item.record_ref.record_type == "capture":
                session = apply_capture_edit(
                    session,
                    item.record_ref.record_id,
                    field_key,
                    value,
                    mode_registry,
                )
            elif item.record_ref.record_type == "pending_capture":
                session = apply_pending_edit(session, item.record_ref.record_id, field_key, value)
            elif item.record_ref.record_type == "measurement":
                session = apply_measurement_edit(
                    session,
                    item.record_ref.parent_id,
                    item.record_ref.record_id,
                    field_key,
                    value,
                    mode_registry,
                )
    return replace(document, session=session)


def _append_unique(values: tuple[str, ...], value: str) -> tuple[str, ...]:
    if value in values:
        return values
    return values + (value,)


def _session_with_edit_invalidation(
    document: SessionDocument,
    item_id: str,
    field_key: str,
    mode_registry: ModeRegistry | None,
) -> SessionRecord:
    item = document.items_by_id.get(item_id)
    if item is None or item.record_ref is None:
        return document.session
    if item.record_ref.record_type == "capture":
        return invalidate_capture_edit(
            document.session,
            item.record_ref.record_id,
            field_key,
            mode_registry,
        )
    if item.record_ref.record_type == "measurement":
        return invalidate_measurement_edit(
            document.session,
            item.record_ref.record_id,
            field_key,
            mode_registry,
        )
    return document.session
