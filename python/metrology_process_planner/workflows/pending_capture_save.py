"""Save pending captures as canonical capture records."""

from __future__ import annotations

from dataclasses import replace

from metrology_process_planner.domains.session import (
    CaptureRecord,
    ModeRegistry,
    PendingCapture,
    SessionRecord,
)
from metrology_process_planner.domains.session.constants import utc_now_iso
from metrology_process_planner.workflows.canvas_interaction_helpers import (
    without_pending,
    without_pending_artifacts,
)
from metrology_process_planner.workflows.capture_replacement import (
    CaptureFactory,
    capture_by_id,
    replacement_for,
    save_replacement_capture,
    without_replacement_metadata,
)
from metrology_process_planner.workflows.mode_capture_defaults import capture_defaults
from metrology_process_planner.workflows.pending_capture_artifacts import (
    capture_with_promoted_artifacts,
)


def save_pending_capture(
    session: SessionRecord,
    pending: PendingCapture,
    label: str,
    notes: str,
    mode_registry: ModeRegistry | None = None,
) -> tuple[SessionRecord, str]:
    """Save one pending capture as a canonical capture record."""

    if replacement_id := replacement_for(pending):
        if capture_by_id(session, replacement_id) is not None:
            return save_replacement_capture(
                session,
                pending,
                replacement_id,
                label,
                notes,
                _capture_factory(mode_registry),
            )
        pending = replace(pending, metadata=without_replacement_metadata(pending))
    capture_id = _next_capture_id(session)
    capture = _capture_from_pending(session, pending, capture_id, label, notes, mode_registry)
    artifacts = without_pending_artifacts(dict(session.artifacts or {}), pending.id)
    warnings = {warning.id: warning for warning in session.warnings}
    capture = capture_with_promoted_artifacts(pending, capture, capture_id, artifacts, warnings)
    updated = replace(
        session,
        captures=session.captures + (capture,),
        pending_captures=without_pending(session, pending.id),
        artifacts=artifacts,
        warnings=tuple(warnings.values()),
        updated_at=utc_now_iso(),
    )
    return _invalidate_new_capture(updated, capture), capture_id


def _capture_factory(mode_registry: ModeRegistry | None) -> CaptureFactory:
    def capture_factory(
        source_session: SessionRecord,
        source_pending: PendingCapture,
        source_capture_id: str,
        source_label: str,
        source_notes: str,
    ) -> CaptureRecord:
        return _capture_from_pending(
            source_session,
            source_pending,
            source_capture_id,
            source_label,
            source_notes,
            mode_registry,
        )

    return capture_factory


def _invalidate_new_capture(
    session: SessionRecord,
    capture: CaptureRecord,
) -> SessionRecord:
    from metrology_process_planner.domains.artifacts.artifact_invalidation import (
        invalidate_new_capture,
    )

    return invalidate_new_capture(session, capture)


def _capture_from_pending(
    session: SessionRecord,
    pending: PendingCapture,
    capture_id: str,
    label: str,
    notes: str,
    mode_registry: ModeRegistry | None = None,
) -> CaptureRecord:
    trace_ids = dict(pending.trace_ids or {})
    trace_ids["capture_trace_id"] = capture_id
    defaults = capture_defaults(session, pending, capture_id, label, mode_registry)
    return CaptureRecord(
        id=capture_id,
        sequence=defaults.sequence,
        label=defaults.label,
        role=defaults.role,
        type=defaults.capture_type,
        geometry=pending.geometry,
        created_at=pending.created_at or utc_now_iso(),
        notes=notes,
        metadata=defaults.metadata,
        trace_ids=trace_ids,
    )


def _next_capture_id(session: SessionRecord) -> str:
    existing_ids = {capture.id for capture in session.captures}
    index = max((_capture_sequence(capture) for capture in session.captures), default=0) + 1
    while f"cap-{index:03d}" in existing_ids:
        index += 1
    return f"cap-{index:03d}"


def _capture_sequence(capture: CaptureRecord) -> int:
    if capture.sequence > 0:
        return capture.sequence
    suffix = capture.id.rsplit("-", 1)[-1]
    return int(suffix) if suffix.isdigit() else 0
