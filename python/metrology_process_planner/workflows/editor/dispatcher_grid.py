"""Grid dataset editor dispatch helpers."""

from __future__ import annotations

from typing import TYPE_CHECKING

from metrology_process_planner.domains.modes.mode_registry import built_in_mode_registry
from metrology_process_planner.domains.session import SessionRecord
from metrology_process_planner.workflows.editor.dispatcher_results import EditorActionResult
from metrology_process_planner.workflows.editor.document import SessionDocument
from metrology_process_planner.workflows.editor.editing import select_item
from metrology_process_planner.workflows.editor.view_models import EditorAction
from metrology_process_planner.workflows.grid_measurement import create_grid_dataset

if TYPE_CHECKING:
    from metrology_process_planner.workflows.editor.dispatcher import EditorActionDispatcher


def create_grid_dataset_action(
    dispatcher: EditorActionDispatcher,
    document: SessionDocument,
    action: EditorAction,
) -> EditorActionResult:
    """Create a grid dataset from payload-selected saved capture anchors."""

    unavailable = _unavailable(document, dispatcher, action)
    if unavailable is not None:
        return unavailable
    payload = dict(action.payload)
    updated = create_grid_dataset(
        document.session,
        str(payload["first_anchor_capture_id"]),
        str(payload["diagonal_anchor_capture_id"]),
        _int(payload["row_count"]),
        _int(payload["column_count"]),
        str(payload.get("label", "")),
    )
    rebuilt = dispatcher._rebuild(updated, document)
    if len(updated.grid_datasets) > len(document.session.grid_datasets):
        rebuilt = select_item(rebuilt, f"grid:{updated.grid_datasets[-1].id}")
        return EditorActionResult("success", rebuilt, "Created grid dataset.")
    return EditorActionResult("warning", rebuilt, _warning_message(document, updated))


def _unavailable(
    document: SessionDocument,
    dispatcher: EditorActionDispatcher,
    action: EditorAction,
) -> EditorActionResult | None:
    mode = (dispatcher._mode_registry or built_in_mode_registry()).definition(
        document.session.mode.value
    )
    if not mode.capabilities.supports_grid_datasets:
        return EditorActionResult("unavailable", document, "Grid datasets are not available.")
    payload = dict(action.payload)
    required = {
        "first_anchor_capture_id",
        "diagonal_anchor_capture_id",
        "row_count",
        "column_count",
    }
    if not required.issubset(payload):
        return EditorActionResult(
            "unavailable",
            document,
            "Create Grid Dataset requires two anchor capture IDs and row/column counts.",
        )
    return _invalid_counts(document, payload)


def _invalid_counts(
    document: SessionDocument,
    payload: dict[str, str],
) -> EditorActionResult | None:
    try:
        rows = _int(payload["row_count"])
        columns = _int(payload["column_count"])
    except ValueError:
        return EditorActionResult("unavailable", document, "Grid rows and columns must be numbers.")
    if rows <= 0 or columns <= 0:
        return EditorActionResult(
            "unavailable",
            document,
            "Grid rows and columns must be positive.",
        )
    return None


def _int(value: str) -> int:
    return int(str(value).strip())


def _warning_message(
    before: SessionDocument,
    updated: SessionRecord,
) -> str:
    existing = {warning.id for warning in before.session.warnings}
    warnings = tuple(warning for warning in updated.warnings if warning.id not in existing)
    if not warnings:
        return "Grid dataset was not created."
    details = "; ".join(f"{warning.code}: {warning.message}" for warning in warnings)
    return f"Grid dataset was not created. {details}"
