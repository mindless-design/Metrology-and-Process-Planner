"""Status text presenter for the unified session editor header."""

from __future__ import annotations

from collections.abc import Callable

from metrology_process_planner.domains.session import session_mode_value
from metrology_process_planner.ui.capture.status import capture_status_from_session
from metrology_process_planner.workflows.editor.document import SessionDocument
from metrology_process_planner.workflows.measurement_completion import measurement_completion_prompt


def status_text(document: SessionDocument) -> str:
    """Return the bottom status strip text for the selected editor item."""

    selected = document.items_by_id[document.selection.selected_item_id]
    for provider in _STATUS_PROVIDERS:
        text = provider(document)
        if text:
            return text
    return f"Ready; selected {selected.label}"


def _measurement_prompt_text(document: SessionDocument) -> str:
    prompt = measurement_completion_prompt(document.session)
    if prompt is not None:
        return f"{prompt.title}: {prompt.message}"
    return ""


def _warning_text(document: SessionDocument) -> str:
    selected = document.items_by_id[document.selection.selected_item_id]
    if document.warning_view_models:
        return f"{len(document.warning_view_models)} warning(s); selected {selected.label}"
    return ""


def _pending_text(document: SessionDocument) -> str:
    if document.pending_capture_item_id:
        return "Pending capture review is waiting in the editor."
    return ""


def _dirty_text(document: SessionDocument) -> str:
    if document.dirty_state.is_dirty:
        return "Unsaved editor changes."
    return ""


def _active_capture_text(document: SessionDocument) -> str:
    capture_status = capture_status_from_session(document.session)
    if not capture_status.armed:
        return ""
    if session_mode_value(document.session.mode) == "fast_batch_capture":
        return (
            "Fast Batch Capture active: hold Left Shift and drag boxes; "
            "captures auto-save. Use Exit Batch Capture when finished."
        )
    return capture_status.message


_STATUS_PROVIDERS: tuple[Callable[[SessionDocument], str], ...] = (
    _measurement_prompt_text,
    _active_capture_text,
    _warning_text,
    _pending_text,
    _dirty_text,
)
