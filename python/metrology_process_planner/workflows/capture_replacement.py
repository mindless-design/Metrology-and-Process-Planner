"""Shared saved-capture replacement workflow helpers."""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import replace

from metrology_process_planner.domains.session import (
    CaptureRecord,
    PendingCapture,
    SessionRecord,
    WorkflowState,
)
from metrology_process_planner.domains.session.constants import utc_now_iso
from metrology_process_planner.workflows.canvas_interaction_helpers import (
    without_pending,
    without_pending_artifacts,
)
from metrology_process_planner.workflows.pending_capture_artifacts import (
    capture_with_promoted_artifacts,
)

CaptureFactory = Callable[[SessionRecord, PendingCapture, str, str, str], CaptureRecord]


def replacement_metadata(session: SessionRecord) -> dict[str, object]:
    """Return pending metadata when the next box capture replaces a saved capture."""

    if (
        session.workflow.stage != "capture"
        or session.workflow.active_primitive != "replacement_box"
    ):
        return {}
    replacement_id = session.workflow.pending_item_ref or ""
    capture = capture_by_id(session, replacement_id)
    if capture is None:
        return {}
    metadata = dict(capture.metadata or {})
    metadata.update(
        {
            "replacement_for": replacement_id,
            "label": capture.label,
            "notes": capture.notes,
            "capture_role": capture.role,
            "capture_type": capture.type,
        }
    )
    return metadata


def review_workflow(session: SessionRecord, metadata: dict[str, object]) -> WorkflowState:
    """Return workflow state after committing a replacement pending capture."""

    if not metadata.get("replacement_for"):
        return session.workflow
    replacement_id = str(metadata["replacement_for"])
    return replace(
        session.workflow,
        active=True,
        stage="review",
        active_primitive="replacement_box",
        pending_item_ref=replacement_id,
        last_saved_capture_id=replacement_id,
    )


def replacement_for(pending: PendingCapture) -> str:
    """Return the saved capture ID targeted by one pending replacement."""

    metadata = dict(pending.metadata or {})
    return str(metadata.get("replacement_for", ""))


def capture_by_id(session: SessionRecord, capture_id: str) -> CaptureRecord | None:
    """Return a saved capture by ID."""

    for capture in session.captures:
        if capture.id == capture_id:
            return capture
    return None


def without_replacement_metadata(pending: PendingCapture) -> dict[str, object]:
    """Return pending metadata with replacement routing removed."""

    metadata = dict(pending.metadata or {})
    metadata.pop("replacement_for", None)
    return metadata


def save_replacement_capture(
    session: SessionRecord,
    pending: PendingCapture,
    capture_id: str,
    label: str,
    notes: str,
    capture_factory: CaptureFactory,
) -> tuple[SessionRecord, str]:
    """Replace an existing capture with one promoted pending capture."""

    existing = capture_by_id(session, capture_id)
    if existing is None:
        raise ValueError(f"Unknown replacement capture: {capture_id}")
    capture = capture_factory(
        session,
        pending,
        capture_id,
        label or existing.label,
        notes or existing.notes,
    )
    capture = replace(
        capture,
        sequence=existing.sequence,
        created_at=existing.created_at,
        metadata={**dict(existing.metadata or {}), **dict(capture.metadata or {})},
    )
    artifacts = without_pending_artifacts(dict(session.artifacts or {}), pending.id)
    warnings = {warning.id: warning for warning in session.warnings}
    capture = capture_with_promoted_artifacts(pending, capture, capture_id, artifacts, warnings)
    return (
        replace(
            session,
            captures=tuple(
                capture if item.id == capture_id else item for item in session.captures
            ),
            pending_captures=without_pending(session, pending.id),
            artifacts=artifacts,
            warnings=tuple(warnings.values()),
            workflow=clear_replacement_workflow(session),
            updated_at=utc_now_iso(),
        ),
        capture_id,
    )


def clear_replacement_workflow(session: SessionRecord) -> WorkflowState:
    """Return idle durable workflow state after replacement completion."""

    return replace(
        session.workflow,
        active=False,
        stage="",
        active_primitive="",
        pending_item_ref=None,
    )
