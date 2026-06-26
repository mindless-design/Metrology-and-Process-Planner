"""Editor and canvas selection rows for Advanced Diagnostics."""

from __future__ import annotations

from metrology_process_planner.workflows.editor.document import SessionDocument


def editor_selection_rows(
    document: SessionDocument | None,
) -> tuple[tuple[str, str], ...]:
    """Return selected editor and canvas state for diagnostics."""

    return (
        ("Selected Editor Item", _selected_editor_item(document)),
        ("Selected Canvas Object", _selected_canvas_objects(document)),
        ("Active Canvas Object", _active_canvas_object(document)),
    )


def _selected_editor_item(document: SessionDocument | None) -> str:
    if document is None:
        return "none"
    selected_id = document.selection.selected_item_id
    item = document.items_by_id.get(selected_id)
    if item is None:
        return selected_id or "none"
    return f"{item.label} ({item.item_id}, {item.status})"


def _selected_canvas_objects(document: SessionDocument | None) -> str:
    if document is None:
        return "none"
    canvas_ids = document.selection.selected_canvas_object_ids
    return ", ".join(canvas_ids) if canvas_ids else "none"


def _active_canvas_object(document: SessionDocument | None) -> str:
    if document is None:
        return "none"
    canvas_id = _first_selected_canvas_id(document)
    if not canvas_id:
        return "none"
    canvas = next(
        (item for item in document.session.canvas_objects if item.id == canvas_id),
        None,
    )
    if canvas is None:
        return f"{canvas_id} (missing)"
    item_id = (document.canvas_object_to_item_id or {}).get(canvas.id, "unmapped")
    return (
        f"{canvas.id} ({canvas.object_type.value}, {canvas.workflow_state.value}, "
        f"record={canvas.record_id}, item={item_id})"
    )


def _first_selected_canvas_id(document: SessionDocument) -> str:
    if document.selection.selected_canvas_object_ids:
        return document.selection.selected_canvas_object_ids[0]
    selected_id = document.selection.selected_item_id
    item = document.items_by_id.get(selected_id)
    if item is None or not item.canvas_object_ids:
        return ""
    return item.canvas_object_ids[0]
