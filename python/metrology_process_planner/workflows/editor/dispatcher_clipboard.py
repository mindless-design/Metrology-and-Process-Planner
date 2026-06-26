"""Clipboard-oriented editor action handlers."""

from __future__ import annotations

import csv
from io import StringIO
from typing import TYPE_CHECKING

from metrology_process_planner.domains.session import CaptureRecord, ModeRegistry, SessionRecord
from metrology_process_planner.persistence.csv_capture_rows import capture_row
from metrology_process_planner.persistence.csv_capture_schema import CAPTURE_SUMMARY_FIELDS
from metrology_process_planner.workflows.editor.dispatcher_results import EditorActionResult
from metrology_process_planner.workflows.editor.dispatcher_support import _record_id
from metrology_process_planner.workflows.editor.document import SessionDocument
from metrology_process_planner.workflows.editor.view_models import EditorAction

if TYPE_CHECKING:
    from metrology_process_planner.workflows.editor.dispatcher import EditorActionDispatcher


def copy_center_coordinate_action(
    _dispatcher: EditorActionDispatcher,
    document: SessionDocument,
    action: EditorAction,
) -> EditorActionResult:
    """Return the selected capture center coordinate for UI clipboard adapters."""

    capture = _capture_for_action(document, action)
    center = capture.geometry.bounds.center if capture and capture.geometry.bounds else None
    if center is None:
        return EditorActionResult("unavailable", document, "No box center is available.")
    return EditorActionResult("success", document, f"Center coordinate: {center.x},{center.y}")


def copy_bounds_action(
    _dispatcher: EditorActionDispatcher,
    document: SessionDocument,
    action: EditorAction,
) -> EditorActionResult:
    """Return the selected capture bounds for UI clipboard adapters."""

    capture = _capture_for_action(document, action)
    bounds = capture.geometry.bounds.normalized() if capture and capture.geometry.bounds else None
    if bounds is None:
        return EditorActionResult("unavailable", document, "No box bounds are available.")
    text = f"{bounds.left},{bounds.bottom},{bounds.right},{bounds.top}"
    return EditorActionResult("success", document, f"Bounds: {text}")


def copy_csv_row_action(
    dispatcher: EditorActionDispatcher,
    document: SessionDocument,
    action: EditorAction,
) -> EditorActionResult:
    """Return the canonical CSV row for the selected capture."""

    capture = _capture_for_action(document, action)
    if capture is None:
        return EditorActionResult("unavailable", document, "No capture row is available.")
    text = _csv_row_text(document.session, capture, dispatcher._mode_registry)
    return EditorActionResult("success", document, f"CSV row: {text}")


def _csv_row_text(
    session: SessionRecord,
    capture: CaptureRecord,
    mode_registry: ModeRegistry | None = None,
) -> str:
    buffer = StringIO()
    writer = csv.DictWriter(buffer, fieldnames=CAPTURE_SUMMARY_FIELDS, lineterminator="")
    writer.writerow(capture_row(session, capture, mode_registry))
    return buffer.getvalue()


def _capture_for_action(document: SessionDocument, action: EditorAction) -> CaptureRecord | None:
    capture_id = _record_id(document, action.item_id)
    for capture in document.session.captures:
        if capture.id == capture_id:
            return capture
    return None
