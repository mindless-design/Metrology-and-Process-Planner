"""Pure editing helpers for session editor documents."""

from __future__ import annotations

from dataclasses import replace
from typing import Optional

from metrology_process_planner.domains.session import CaptureRecord, PendingCapture, SessionRecord
from metrology_process_planner.workflows.editor.document import (
    DirtyState,
    EditorSelectionState,
    SessionDocument,
)
from metrology_process_planner.workflows.editor.measurement_editing import (
    replace_measurement_field,
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
    return replace(document, dirty_state=dirty)


def mark_pending_dirty(document: SessionDocument) -> SessionDocument:
    """Return a document with pending capture edits marked dirty."""

    dirty = replace(document.dirty_state, is_dirty=True, unsaved_pending_capture=True)
    return replace(document, dirty_state=dirty)


def mark_clean(document: SessionDocument, revision: int) -> SessionDocument:
    """Return a document with dirty state cleared after a successful save."""

    return replace(document, dirty_state=DirtyState(last_saved_revision=revision))


def apply_metadata_edits(document: SessionDocument) -> SessionDocument:
    """Return a document whose canonical session includes tracked metadata edits."""

    session = document.session
    for item_id, field_key, value in document.dirty_state.unsaved_metadata_edits:
        item = document.items_by_id.get(item_id)
        if item_id == "dashboard" and field_key in {"name", "session_name"}:
            session = replace(session, name=value)
        elif item is not None and item.record_ref is not None:
            if item.record_ref.record_type == "capture":
                session = _apply_capture_edit(session, item.record_ref.record_id, field_key, value)
            elif item.record_ref.record_type == "pending_capture":
                session = _apply_pending_edit(session, item.record_ref.record_id, field_key, value)
            elif item.record_ref.record_type == "measurement":
                session = _apply_measurement_edit(
                    session,
                    item.record_ref.parent_id,
                    item.record_ref.record_id,
                    field_key,
                    value,
                )
    return replace(document, session=session)


def _append_unique(values: tuple[str, ...], value: str) -> tuple[str, ...]:
    if value in values:
        return values
    return values + (value,)


def _apply_capture_edit(
    session: SessionRecord,
    capture_id: str,
    field_key: str,
    value: str,
) -> SessionRecord:
    captures = tuple(
        _replace_capture_field(capture, field_key, value)
        if capture.id == capture_id
        else capture
        for capture in session.captures
    )
    return replace(session, captures=captures)


def _replace_capture_field(capture: CaptureRecord, field_key: str, value: str) -> CaptureRecord:
    if field_key == "label":
        return replace(capture, label=value)
    if field_key == "notes":
        return replace(capture, notes=value)
    if field_key == "type":
        return replace(capture, type=value)
    metadata = dict(capture.metadata or {})
    metadata[field_key] = value
    return replace(capture, metadata=metadata)


def _apply_pending_edit(
    session: SessionRecord,
    pending_id: str,
    field_key: str,
    value: str,
) -> SessionRecord:
    pending_captures = tuple(
        _replace_pending_field(pending, field_key, value)
        if pending.id == pending_id
        else pending
        for pending in session.pending_captures
    )
    return replace(session, pending_captures=pending_captures)


def _replace_pending_field(
    pending: PendingCapture,
    field_key: str,
    value: str,
) -> PendingCapture:
    metadata = dict(pending.metadata or {})
    metadata[field_key] = value
    return replace(pending, metadata=metadata)


def _apply_measurement_edit(
    session: SessionRecord,
    capture_item_id: Optional[str],
    measurement_id: str,
    field_key: str,
    value: str,
) -> SessionRecord:
    capture_id = _record_id_from_item_id(capture_item_id)
    captures = tuple(
        _replace_measurement_on_capture(capture, measurement_id, field_key, value)
        if capture_id is None or capture.id == capture_id
        else capture
        for capture in session.captures
    )
    return replace(session, captures=captures)


def _replace_measurement_on_capture(
    capture: CaptureRecord,
    measurement_id: str,
    field_key: str,
    value: str,
) -> CaptureRecord:
    measurements = tuple(
        replace_measurement_field(measurement, field_key, value)
        if measurement.id == measurement_id
        else measurement
        for measurement in capture.measurements
    )
    return replace(capture, measurements=measurements)


def _record_id_from_item_id(item_id: Optional[str]) -> Optional[str]:
    if item_id is None:
        return None
    if ":" not in item_id:
        return item_id
    return item_id.split(":", 1)[1]
