"""Composite pending-capture editor action helpers."""

from __future__ import annotations

from typing import Any, Optional, Protocol

from metrology_process_planner.domains.session import PendingCapture, SessionRecord
from metrology_process_planner.workflows.compound_capture import save_composite_capture
from metrology_process_planner.workflows.compound_capture_models import (
    DiscardCompositeCommand,
    ExitCompositeCommand,
    RetakeInnerFeatureCommand,
    RetakeParentCommand,
    SaveCompositeCaptureCommand,
)
from metrology_process_planner.workflows.compound_capture_records import (
    pending_composite_from_pending,
)
from metrology_process_planner.workflows.compound_capture_review import (
    discard_composite_capture,
    exit_composite_capture,
    retake_inner_feature,
    retake_parent_capture,
)
from metrology_process_planner.workflows.editor.dispatcher_results import EditorActionResult
from metrology_process_planner.workflows.editor.dispatcher_support import (
    _payload_value,
    _record_id,
)
from metrology_process_planner.workflows.editor.document import SessionDocument
from metrology_process_planner.workflows.editor.editing import apply_metadata_edits
from metrology_process_planner.workflows.editor.view_models import EditorAction


class _CompositeDispatcher(Protocol):
    def _rebuild(self, session: SessionRecord, document: SessionDocument) -> SessionDocument:
        """Rebuild a document after a workflow mutation."""


def composite_save_action(
    dispatcher: _CompositeDispatcher,
    document: SessionDocument,
    action: EditorAction,
) -> EditorActionResult:
    """Save a pending composite capture from the editor."""

    document = apply_metadata_edits(document)
    pending_id = _record_id(document, action.item_id)
    pending = _pending_by_id(document.session, pending_id)
    metadata = _pending_metadata(pending)
    command = SaveCompositeCaptureCommand(
        pending_id,
        _payload_value(action, "label") or metadata.get("label", ""),
        _payload_value(action, "notes") or metadata.get("notes", ""),
        metadata,
    )
    try:
        result = save_composite_capture(document.session, command)
    except ValueError as exc:
        return EditorActionResult("warning", document, str(exc))
    status = "warning" if result.warnings else "success"
    return EditorActionResult(
        status,
        dispatcher._rebuild(result.session, document),
        "Saved composite capture.",
    )


def composite_retake_inner_action(
    dispatcher: _CompositeDispatcher,
    document: SessionDocument,
    action: EditorAction,
) -> EditorActionResult:
    """Retake only the inner feature for a pending composite."""

    command = RetakeInnerFeatureCommand(_record_id(document, action.item_id))
    session = retake_inner_feature(document.session, command)
    return EditorActionResult(
        "success",
        dispatcher._rebuild(session, document),
        "Retake inner feature.",
    )


def composite_retake_parent_action(
    dispatcher: _CompositeDispatcher,
    document: SessionDocument,
    action: EditorAction,
) -> EditorActionResult:
    """Retake the parent site box for a pending composite."""

    command = RetakeParentCommand(_record_id(document, action.item_id))
    session = retake_parent_capture(document.session, command)
    return EditorActionResult(
        "success",
        dispatcher._rebuild(session, document),
        "Retake site box.",
    )


def composite_discard_action(
    dispatcher: _CompositeDispatcher,
    document: SessionDocument,
    action: EditorAction,
) -> EditorActionResult:
    """Discard a pending composite capture."""

    command = DiscardCompositeCommand(_record_id(document, action.item_id))
    session = discard_composite_capture(document.session, command)
    return EditorActionResult(
        "success",
        dispatcher._rebuild(session, document),
        "Discarded composite capture.",
    )


def composite_exit_action(
    dispatcher: _CompositeDispatcher,
    document: SessionDocument,
    action: EditorAction,
) -> EditorActionResult:
    """Exit composite capture mode without deleting pending review state."""

    command = ExitCompositeCommand(_record_id(document, action.item_id))
    session = exit_composite_capture(document.session, command)
    return EditorActionResult(
        "success",
        dispatcher._rebuild(session, document),
        "Exited composite capture.",
    )


def pending_is_composite(document: SessionDocument, item_id: str) -> bool:
    """Return whether an editor item references a compound pending capture."""

    return pending_id_is_composite(document.session, _record_id(document, item_id))


def pending_id_is_composite(session: SessionRecord, pending_id: str) -> bool:
    """Return whether a pending capture stores compound metadata."""

    pending = _find_pending(session, pending_id)
    return bool(pending is not None and dict(pending.metadata or {}).get("compound"))


def _pending_by_id(session: SessionRecord, pending_id: str) -> PendingCapture:
    pending = _find_pending(session, pending_id)
    if pending is None:
        raise ValueError(f"Pending capture {pending_id} was not found.")
    return pending


def _find_pending(session: SessionRecord, pending_id: str) -> Optional[PendingCapture]:
    for pending in session.pending_captures:
        if pending.id == pending_id:
            return pending
    return None


def _pending_metadata(pending: PendingCapture) -> dict[str, Any]:
    composite = pending_composite_from_pending(pending)
    payload = dict(getattr(pending, "metadata", {}) or {})
    metadata = dict(payload)
    metadata.pop("compound", None)
    if composite.feature is not None:
        metadata["feature_id"] = composite.feature.id
    return metadata
