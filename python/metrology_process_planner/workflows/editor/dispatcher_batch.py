"""Fast Batch Capture editor actions."""

from __future__ import annotations

from dataclasses import replace
from typing import TYPE_CHECKING

from metrology_process_planner.domains.session import session_mode_value
from metrology_process_planner.domains.session.constants import utc_now_iso
from metrology_process_planner.workflows.editor.dispatcher_results import EditorActionResult
from metrology_process_planner.workflows.editor.dispatcher_support import _payload_value
from metrology_process_planner.workflows.editor.document import SessionDocument
from metrology_process_planner.workflows.editor.view_models import EditorAction

if TYPE_CHECKING:
    from metrology_process_planner.workflows.editor.dispatcher import EditorActionDispatcher


def batch_rename_action(
    dispatcher: EditorActionDispatcher,
    document: SessionDocument,
    action: EditorAction,
) -> EditorActionResult:
    """Rename saved Fast Batch captures with a stable generated label series."""

    if session_mode_value(document.session.mode) != "fast_batch_capture":
        return EditorActionResult(
            "unavailable",
            document,
            "Batch Rename is only available in Fast Batch Capture mode.",
        )
    if not document.session.captures:
        return EditorActionResult("unavailable", document, "No saved captures to rename.")

    prefix = _payload_value(action, "prefix").strip() or "Capture"
    start = _positive_int(_payload_value(action, "start"), 1)
    padding = _positive_int(_payload_value(action, "padding"), 3)
    timestamp = utc_now_iso()
    renamed = tuple(
        replace(
            capture,
            label=f"{prefix} {index:0{padding}d}",
            metadata=_renamed_metadata(capture.metadata, f"{prefix} {index:0{padding}d}"),
            modified_at=timestamp,
        )
        for index, capture in enumerate(document.session.captures, start=start)
    )
    session = replace(document.session, captures=renamed, updated_at=timestamp)
    return EditorActionResult(
        "success",
        dispatcher._rebuild(session, document),
        f"Renamed {len(renamed)} batch captures.",
    )


def _positive_int(value: str, fallback: int) -> int:
    try:
        parsed = int(value)
    except ValueError:
        return fallback
    return parsed if parsed > 0 else fallback


def _renamed_metadata(metadata: object, label: str) -> dict[str, object]:
    updated = dict(metadata or {}) if isinstance(metadata, dict) else {}
    updated["label"] = label
    return updated
