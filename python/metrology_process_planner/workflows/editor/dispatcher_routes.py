"""Route-table helpers for editor action dispatch."""

from __future__ import annotations

from collections.abc import Callable
from typing import TYPE_CHECKING

from metrology_process_planner.workflows.editor.dispatcher_artifact_ops import (
    relink_artifact,
)
from metrology_process_planner.workflows.editor.dispatcher_basic import (
    copy_bounds_action,
    copy_center_coordinate_action,
    copy_csv_row_action,
    edit_metadata_action,
    export_csv_action,
    open_output_folder_action,
    replace_capture_action,
    select_canvas_action,
    select_item_action,
    update_metadata_field_action,
)
from metrology_process_planner.workflows.editor.dispatcher_batch import batch_rename_action
from metrology_process_planner.workflows.editor.dispatcher_composite import (
    composite_discard_action,
    composite_exit_action,
    composite_retake_inner_action,
    composite_retake_parent_action,
    composite_save_action,
)
from metrology_process_planner.workflows.editor.dispatcher_grid import create_grid_dataset_action
from metrology_process_planner.workflows.editor.dispatcher_overviews import (
    add_user_label_action,
    generate_grid_overview_action,
    generate_metrology_overview_action,
    generate_session_overview_action,
    regenerate_overview_action,
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


def _relink_artifact_action(
    dispatcher: EditorActionDispatcher,
    document: SessionDocument,
    action: EditorAction,
) -> EditorActionResult:
    return relink_artifact(dispatcher, document, action)


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
    EditorActionType.EDIT_METADATA: edit_metadata_action,
    EditorActionType.UPDATE_METADATA_FIELD: update_metadata_field_action,
    EditorActionType.BATCH_RENAME: batch_rename_action,
    EditorActionType.EXPORT_CSV: export_csv_action,
    EditorActionType.OPEN_OUTPUT_FOLDER: open_output_folder_action,
    EditorActionType.SELECT_ITEM: select_item_action,
    EditorActionType.SELECT_CANVAS_OBJECT: select_canvas_action,
    EditorActionType.PENDING_SAVE: _pending_save_action,
    EditorActionType.PENDING_RETAKE: pending_retake_action,
    EditorActionType.PENDING_DISCARD: pending_discard_action,
    EditorActionType.COMPOSITE_SAVE: composite_save_action,
    EditorActionType.COMPOSITE_RETAKE_INNER: composite_retake_inner_action,
    EditorActionType.COMPOSITE_RETAKE_PARENT: composite_retake_parent_action,
    EditorActionType.COMPOSITE_DISCARD: composite_discard_action,
    EditorActionType.COMPOSITE_EXIT: composite_exit_action,
    EditorActionType.REGENERATE_ARTIFACT: _regenerate_artifact_action,
    EditorActionType.RELINK_ARTIFACT: _relink_artifact_action,
    EditorActionType.ADD_MEASUREMENT: _add_measurement_action,
    EditorActionType.GENERATE_SESSION_OVERVIEW: generate_session_overview_action,
    EditorActionType.GENERATE_METROLOGY_OVERVIEW: generate_metrology_overview_action,
    EditorActionType.GENERATE_GRID_OVERVIEW: generate_grid_overview_action,
    EditorActionType.CREATE_GRID_DATASET: create_grid_dataset_action,
    EditorActionType.REGENERATE_OVERVIEW: regenerate_overview_action,
    EditorActionType.ADD_USER_LABEL: add_user_label_action,
    EditorActionType.SAVE_MEASUREMENT: _save_measurement_action,
    EditorActionType.RETAKE_MEASUREMENT_LINE: _retake_measurement_action,
    EditorActionType.DISCARD_MEASUREMENT: _discard_measurement_action,
    EditorActionType.ATTACH_RECIPE: attach_recipe_action,
    EditorActionType.DETACH_RECIPE: _detach_recipe_action,
    EditorActionType.VALIDATE_PROCESS_CONTEXT: _validate_process_context_action,
    EditorActionType.REFRESH_RECIPE_FINGERPRINT: _refresh_recipe_fingerprint_action,
    EditorActionType.REGENERATE_PROCESS_OUTPUT: regenerate_process_output_action,
    EditorActionType.COPY_CENTER_COORDINATE: copy_center_coordinate_action,
    EditorActionType.COPY_BOUNDS: copy_bounds_action,
    EditorActionType.COPY_CSV_ROW: copy_csv_row_action,
    EditorActionType.REPLACE_SITE_BOX: replace_capture_action,
    EditorActionType.REPLACE_INNER_FEATURE: replace_capture_action,
}
