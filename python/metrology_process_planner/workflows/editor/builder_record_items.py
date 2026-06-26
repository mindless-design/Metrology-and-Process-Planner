"""Record-backed editor item builders for captures and pending captures."""

from __future__ import annotations

from collections.abc import Mapping

from metrology_process_planner.domains.session import CaptureRecord, ModeRegistry, SessionRecord
from metrology_process_planner.workflows.editor.builder_artifact_refs import (
    _artifact_refs,
    _artifact_refs_for_owner,
)
from metrology_process_planner.workflows.editor.builder_canvas import (
    capture_canvas_ids,
    pending_canvas_ids,
)
from metrology_process_planner.workflows.editor.document import SessionItem, SessionItemKind
from metrology_process_planner.workflows.editor.references import RecordRef
from metrology_process_planner.workflows.editor.view_models import WarningViewModel


def pending_item(
    session: SessionRecord,
    pending_id: str,
    warning_artifacts: Mapping[str, WarningViewModel],
    mode_registry: ModeRegistry | None,
) -> SessionItem:
    """Return the editor item for one pending capture."""

    pending = next(item for item in session.pending_captures if item.id == pending_id)
    artifact_refs = _artifact_refs_for_owner(
        session,
        "pending_capture",
        pending.id,
        mode_registry,
    ) or _artifact_refs((("crop", pending.image_artifact_path),), warning_artifacts)
    return SessionItem(
        item_id=f"pending:{pending.id}",
        kind=SessionItemKind.PENDING_CAPTURE,
        label=f"Pending Capture {pending.id}",
        role="pending_capture",
        status="pending",
        parent_id=pending.parent_id,
        record_ref=RecordRef("pending_capture", pending.id, pending.parent_id),
        canvas_object_ids=pending_canvas_ids(session, pending.canvas_object_id),
        artifact_refs=artifact_refs,
    )


def capture_item(
    session: SessionRecord,
    capture: CaptureRecord,
    mode_registry: ModeRegistry | None,
) -> SessionItem:
    """Return the editor item for one saved capture."""

    return SessionItem(
        item_id=f"capture:{capture.id}",
        kind=SessionItemKind.SAVED_CAPTURE,
        label=capture.label or capture.id,
        role=capture.type,
        record_ref=RecordRef("capture", capture.id),
        canvas_object_ids=capture_canvas_ids(session, capture.id),
        artifact_refs=_artifact_refs_for_owner(session, "capture", capture.id, mode_registry),
    )
