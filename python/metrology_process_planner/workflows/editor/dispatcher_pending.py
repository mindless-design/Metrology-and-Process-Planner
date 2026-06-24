"""Pending-capture editor action helpers."""

from __future__ import annotations

from typing import Protocol

from metrology_process_planner.domains.session import SessionRecord
from metrology_process_planner.workflows.editor.dispatcher_results import EditorActionResult
from metrology_process_planner.workflows.editor.dispatcher_support import (
    _empty_context,
    _record_id,
)
from metrology_process_planner.workflows.editor.document import SessionDocument
from metrology_process_planner.workflows.editor.view_models import EditorAction
from metrology_process_planner.workflows.pending_capture_review import PendingCaptureReviewService


class _PendingDispatcher(Protocol):
    _pending: PendingCaptureReviewService

    def _rebuild(self, session: SessionRecord, document: SessionDocument) -> SessionDocument:
        """Rebuild a document after a workflow mutation."""


def pending_retake_action(
    dispatcher: _PendingDispatcher,
    document: SessionDocument,
    action: EditorAction,
) -> EditorActionResult:
    """Dispatch pending retake."""

    result = dispatcher._pending.retake_pending(
        document.session,
        _empty_context(),
        _record_id(document, action.item_id),
    )
    return EditorActionResult(
        "success",
        dispatcher._rebuild(result.session, document),
        "Retake pending capture.",
    )


def pending_discard_action(
    dispatcher: _PendingDispatcher,
    document: SessionDocument,
    action: EditorAction,
) -> EditorActionResult:
    """Dispatch pending discard."""

    result = dispatcher._pending.discard_pending(
        document.session,
        _empty_context(),
        _record_id(document, action.item_id),
    )
    return EditorActionResult(
        "success",
        dispatcher._rebuild(result.session, document),
        "Discarded pending capture.",
    )
