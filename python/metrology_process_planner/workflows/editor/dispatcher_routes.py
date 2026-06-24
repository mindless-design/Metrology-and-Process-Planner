"""Route-table helpers for editor action dispatch."""

from __future__ import annotations

from collections.abc import Callable
from typing import TYPE_CHECKING

from metrology_process_planner.workflows.editor.dispatcher_composite import (
    composite_discard_action,
    composite_exit_action,
    composite_retake_inner_action,
    composite_retake_parent_action,
    composite_save_action,
)
from metrology_process_planner.workflows.editor.dispatcher_pending import (
    pending_discard_action,
    pending_retake_action,
)
from metrology_process_planner.workflows.editor.dispatcher_process_context import (
    attach_recipe_action,
    detach_recipe_action,
    refresh_recipe_fingerprint_action,
    regenerate_process_output_action,
    validate_process_context_action,
)
from metrology_process_planner.workflows.editor.dispatcher_results import EditorActionResult
from metrology_process_planner.workflows.editor.dispatcher_support import _payload_value
from metrology_process_planner.workflows.editor.document import SessionDocument
from metrology_process_planner.workflows.editor.view_models import EditorAction, EditorActionType

if TYPE_CHECKING:
    from metrology_process_planner.workflows.editor.dispatcher import EditorActionDispatcher


ActionHandler = Callable[
    ["EditorActionDispatcher", SessionDocument, EditorAction],
    EditorActionResult,
]


def dispatch_mapped_action(
    dispatcher: EditorActionDispatcher,
    document: SessionDocument,
    action: EditorAction,
) -> EditorActionResult | None:
    """Dispatch an action through the explicit editor route table."""

    handler = _ACTION_HANDLERS.get(action.action_type)
    return None if handler is None else handler(dispatcher, document, action)


def _save_action(
    dispatcher: EditorActionDispatcher,
    document: SessionDocument,
    _action: EditorAction,
) -> EditorActionResult:
    return dispatcher._save(document)


def _export_csv_action(
    dispatcher: EditorActionDispatcher,
    document: SessionDocument,
    _action: EditorAction,
) -> EditorActionResult:
    return dispatcher._export_csv(document)


def _open_output_folder_action(
    dispatcher: EditorActionDispatcher,
    document: SessionDocument,
    _action: EditorAction,
) -> EditorActionResult:
    return dispatcher._open_output_folder(document)


def _select_item_action(
    dispatcher: EditorActionDispatcher,
    document: SessionDocument,
    action: EditorAction,
) -> EditorActionResult:
    return dispatcher._select_item(document, action.item_id)


def _select_canvas_action(
    dispatcher: EditorActionDispatcher,
    document: SessionDocument,
    action: EditorAction,
) -> EditorActionResult:
    return dispatcher._select_canvas(document, _payload_value(action, "canvas_object_id"))


def _pending_save_action(
    dispatcher: EditorActionDispatcher,
    document: SessionDocument,
    action: EditorAction,
) -> EditorActionResult:
    return dispatcher._pending_save(document, action)


def _regenerate_artifact_action(
    dispatcher: EditorActionDispatcher,
    document: SessionDocument,
    action: EditorAction,
) -> EditorActionResult:
    return dispatcher._regenerate_artifact(document, action)


def _add_measurement_action(
    dispatcher: EditorActionDispatcher,
    document: SessionDocument,
    action: EditorAction,
) -> EditorActionResult:
    return dispatcher._add_measurement(document, action)


def _save_measurement_action(
    dispatcher: EditorActionDispatcher,
    document: SessionDocument,
    _action: EditorAction,
) -> EditorActionResult:
    return dispatcher._save(document)


def _retake_measurement_action(
    dispatcher: EditorActionDispatcher,
    document: SessionDocument,
    action: EditorAction,
) -> EditorActionResult:
    return dispatcher._retake_measurement(document, action)


def _discard_measurement_action(
    dispatcher: EditorActionDispatcher,
    document: SessionDocument,
    action: EditorAction,
) -> EditorActionResult:
    return dispatcher._discard_measurement(document, action)


def _detach_recipe_action(
    dispatcher: EditorActionDispatcher,
    document: SessionDocument,
    _action: EditorAction,
) -> EditorActionResult:
    return detach_recipe_action(dispatcher, document)


def _validate_process_context_action(
    dispatcher: EditorActionDispatcher,
    document: SessionDocument,
    _action: EditorAction,
) -> EditorActionResult:
    return validate_process_context_action(dispatcher, document)


def _refresh_recipe_fingerprint_action(
    dispatcher: EditorActionDispatcher,
    document: SessionDocument,
    _action: EditorAction,
) -> EditorActionResult:
    return refresh_recipe_fingerprint_action(dispatcher, document)


_ACTION_HANDLERS: dict[EditorActionType, ActionHandler] = {
    EditorActionType.SAVE_EDITS: _save_action,
    EditorActionType.EXPORT_CSV: _export_csv_action,
    EditorActionType.OPEN_OUTPUT_FOLDER: _open_output_folder_action,
    EditorActionType.SELECT_ITEM: _select_item_action,
    EditorActionType.SELECT_CANVAS_OBJECT: _select_canvas_action,
    EditorActionType.PENDING_SAVE: _pending_save_action,
    EditorActionType.PENDING_RETAKE: pending_retake_action,
    EditorActionType.PENDING_DISCARD: pending_discard_action,
    EditorActionType.COMPOSITE_SAVE: composite_save_action,
    EditorActionType.COMPOSITE_RETAKE_INNER: composite_retake_inner_action,
    EditorActionType.COMPOSITE_RETAKE_PARENT: composite_retake_parent_action,
    EditorActionType.COMPOSITE_DISCARD: composite_discard_action,
    EditorActionType.COMPOSITE_EXIT: composite_exit_action,
    EditorActionType.REGENERATE_ARTIFACT: _regenerate_artifact_action,
    EditorActionType.ADD_MEASUREMENT: _add_measurement_action,
    EditorActionType.SAVE_MEASUREMENT: _save_measurement_action,
    EditorActionType.RETAKE_MEASUREMENT_LINE: _retake_measurement_action,
    EditorActionType.DISCARD_MEASUREMENT: _discard_measurement_action,
    EditorActionType.ATTACH_RECIPE: attach_recipe_action,
    EditorActionType.DETACH_RECIPE: _detach_recipe_action,
    EditorActionType.VALIDATE_PROCESS_CONTEXT: _validate_process_context_action,
    EditorActionType.REFRESH_RECIPE_FINGERPRINT: _refresh_recipe_fingerprint_action,
    EditorActionType.REGENERATE_PROCESS_OUTPUT: regenerate_process_output_action,
}
