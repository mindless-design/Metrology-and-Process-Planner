"""Basic editor action handlers shared by the dispatcher route table."""

from __future__ import annotations

from dataclasses import replace
from typing import TYPE_CHECKING

from metrology_process_planner.domains.session import CaptureRecord
from metrology_process_planner.workflows.editor.adapter_metadata import metadata_fields_for_item
from metrology_process_planner.workflows.editor.csv_export_artifacts import with_csv_export_artifact
from metrology_process_planner.workflows.editor.dispatcher_clipboard import (
    copy_bounds_action,
    copy_center_coordinate_action,
    copy_csv_row_action,
)
from metrology_process_planner.workflows.editor.dispatcher_results import EditorActionResult
from metrology_process_planner.workflows.editor.dispatcher_support import _payload_value, _record_id
from metrology_process_planner.workflows.editor.document import SessionDocument
from metrology_process_planner.workflows.editor.editing import (
    mark_metadata_edit,
    select_canvas_object,
    select_item,
)
from metrology_process_planner.workflows.editor.view_models import EditorAction, EditorActionType

if TYPE_CHECKING:
    from metrology_process_planner.workflows.editor.dispatcher import EditorActionDispatcher

__all__ = [
    "copy_bounds_action",
    "copy_center_coordinate_action",
    "copy_csv_row_action",
    "edit_metadata_action",
    "export_csv_action",
    "open_output_folder_action",
    "replace_capture_action",
    "select_canvas_action",
    "select_item_action",
    "update_metadata_field_action",
]


def export_csv_action(
    dispatcher: EditorActionDispatcher,
    document: SessionDocument,
    _action: EditorAction,
) -> EditorActionResult:
    """Export captures from the selected document to CSV."""

    if dispatcher._paths is None:
        return EditorActionResult("unavailable", document, "No session folder is configured.")
    destination = dispatcher._csv.export(document.session, dispatcher._paths.capture_csv)
    session = with_csv_export_artifact(
        document.session,
        dispatcher._paths,
        destination,
        dispatcher._mode_registry,
    )
    return EditorActionResult(
        "success",
        dispatcher._rebuild(session, document),
        "Exported capture CSV.",
        destination,
    )


def open_output_folder_action(
    dispatcher: EditorActionDispatcher,
    document: SessionDocument,
    _action: EditorAction,
) -> EditorActionResult:
    """Resolve the current session output folder."""

    if dispatcher._paths is None:
        return EditorActionResult("unavailable", document, "No session folder is configured.")
    return EditorActionResult(
        "success",
        document,
        "Output folder path resolved.",
        dispatcher._paths.folder,
    )


def edit_metadata_action(
    _dispatcher: EditorActionDispatcher,
    document: SessionDocument,
    action: EditorAction,
) -> EditorActionResult:
    """Keep metadata editing in the unified editor surface."""

    selected = select_item(document, action.item_id) if action.item_id else document
    return EditorActionResult("success", selected, "Metadata editor ready.")


def update_metadata_field_action(
    dispatcher: EditorActionDispatcher,
    document: SessionDocument,
    action: EditorAction,
) -> EditorActionResult:
    """Track one inline metadata edit from the inspector."""

    item_id = action.item_id or document.selection.selected_item_id
    field_key = _payload_value(action, "field_key")
    value = _payload_value(action, "value")
    if not field_key:
        return EditorActionResult("unavailable", document, "Metadata update requires a field key.")
    item = document.items_by_id.get(item_id)
    if item is None:
        return EditorActionResult("unavailable", document, "Metadata update requires an item.")
    fields = metadata_fields_for_item(document.session, item, dispatcher._mode_registry)
    field = next((candidate for candidate in fields if candidate.key == field_key), None)
    if field is None:
        return EditorActionResult(
            "unavailable",
            document,
            f"Metadata field is not available: {field_key}",
        )
    if field.read_only:
        return EditorActionResult(
            "unavailable",
            document,
            f"Metadata field is read-only: {field.label}",
        )
    edited = mark_metadata_edit(document, item_id, field_key, value, dispatcher._mode_registry)
    edited = select_item(edited, item_id)
    return EditorActionResult("success", edited, f"Updated {field.label}.")


def select_item_action(
    dispatcher: EditorActionDispatcher,
    document: SessionDocument,
    action: EditorAction,
) -> EditorActionResult:
    """Select one normalized editor item."""

    selected = select_item(document, action.item_id)
    canvas_ids = selected.selection.selected_canvas_object_ids
    if canvas_ids and dispatcher._selection is not None:
        sync = dispatcher._selection.select_from_editor(selected.session, canvas_ids[0])
        selected = dispatcher._rebuild(sync.session, selected)
    return EditorActionResult("success", selected, "Selected editor item.")


def select_canvas_action(
    dispatcher: EditorActionDispatcher,
    document: SessionDocument,
    action: EditorAction,
) -> EditorActionResult:
    """Select the editor item linked to one canvas object."""

    canvas_object_id = _payload_value(action, "canvas_object_id")
    selected = select_canvas_object(document, canvas_object_id)
    if dispatcher._selection is not None:
        sync = dispatcher._selection.select_from_canvas(selected.session, canvas_object_id)
        selected = dispatcher._rebuild(sync.session, selected)
    return EditorActionResult("success", selected, "Selected canvas object.")


def replace_capture_action(
    dispatcher: EditorActionDispatcher,
    document: SessionDocument,
    action: EditorAction,
) -> EditorActionResult:
    """Arm the shared box-capture workflow to replace one saved capture."""

    if action.action_type is EditorActionType.REPLACE_INNER_FEATURE:
        return EditorActionResult(
            "unavailable",
            document,
            f"{action.label} is unavailable until the shared capture replacement workflow "
            "supports inner features.",
        )
    capture = _capture_for_action(document, action)
    if capture is None or capture.geometry.bounds is None:
        return EditorActionResult(
            "unavailable",
            document,
            "Only saved box captures can be replaced.",
        )
    workflow = replace(
        document.session.workflow,
        active=True,
        stage="capture",
        active_primitive="replacement_box",
        pending_item_ref=capture.id,
        last_saved_capture_id=capture.id,
    )
    session = replace(document.session, workflow=workflow)
    return EditorActionResult(
        "success",
        dispatcher._rebuild(session, document),
        f"Armed replacement capture for {capture.label}.",
    )


def _capture_for_action(document: SessionDocument, action: EditorAction) -> CaptureRecord | None:
    capture_id = _record_id(document, action.item_id)
    for capture in document.session.captures:
        if capture.id == capture_id:
            return capture
    return None
