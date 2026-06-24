"""Review-stage operations for pending compound captures."""

from __future__ import annotations

from dataclasses import replace

from metrology_process_planner.domains.session import (
    CanvasObjectType,
    SessionRecord,
    WorkflowState,
    utc_now_iso,
)
from metrology_process_planner.workflows.canvas_interaction_helpers import without_pending
from metrology_process_planner.workflows.canvas_state import (
    remove_canvas_object,
    set_active_parent_object,
)
from metrology_process_planner.workflows.compound_capture_models import (
    CompoundCaptureRequest,
    DiscardCompositeCommand,
    ExitCompositeCommand,
    RetakeInnerFeatureCommand,
    RetakeParentCommand,
)
from metrology_process_planner.workflows.compound_capture_pending import (
    replace_pending,
    required_pending,
)
from metrology_process_planner.workflows.compound_capture_records import (
    compound_payload,
    pending_composite_from_pending,
)


def retake_inner_feature(
    session: SessionRecord,
    command: RetakeInnerFeatureCommand,
) -> SessionRecord:
    """Remove only the pending child feature and keep the parent active."""

    pending_id = command.pending_id
    pending = required_pending(session, pending_id)
    composite = pending_composite_from_pending(pending)
    if composite.feature is None:
        return _arm_child(session, pending_id, composite.request)
    session = replace(
        session,
        canvas_objects=tuple(
            item for item in session.canvas_objects if item.parent_id != pending.canvas_object_id
        ),
        workflow=replace(
            session.workflow,
            active=True,
            stage=f"{composite.request.sequence_type}:child",
            active_mode=composite.request.mode_id,
            active_primitive=_child_primitive(composite.request).value,
            pending_item_ref=pending.id,
        ),
    )
    pending = replace(pending, metadata={"compound": compound_payload(composite.request)})
    session = replace_pending(session, pending)
    return set_active_parent_object(session, pending.canvas_object_id)


def retake_parent_capture(
    session: SessionRecord,
    command: RetakeParentCommand,
) -> SessionRecord:
    """Remove the pending composite and rearm the parent site box."""

    pending_id = command.pending_id
    pending = required_pending(session, pending_id)
    composite = pending_composite_from_pending(pending)
    session = discard_composite_capture(session, DiscardCompositeCommand(pending_id))
    return replace(
        session,
        workflow=replace(
            session.workflow,
            active=True,
            stage=f"{composite.request.sequence_type}:parent",
            active_mode=composite.request.mode_id,
            active_primitive=CanvasObjectType.SITE_BOX.value,
            pending_item_ref="",
        ),
    )


def discard_composite_capture(
    session: SessionRecord,
    command: DiscardCompositeCommand,
) -> SessionRecord:
    """Remove a pending composite parent and any child overlays."""

    pending_id = command.pending_id
    pending = required_pending(session, pending_id)
    for item in tuple(session.canvas_objects):
        if item.id == pending.canvas_object_id or item.parent_id == pending.canvas_object_id:
            session = remove_canvas_object(session, item.id)
    return replace(
        session,
        pending_captures=without_pending(session, pending.id),
        workflow=WorkflowState(),
        updated_at=utc_now_iso(),
    )


def exit_composite_capture(
    session: SessionRecord,
    command: ExitCompositeCommand,
) -> SessionRecord:
    """Clear armed composite state while preserving pending review records."""

    pending_id = command.pending_id
    pending = required_pending(session, pending_id)
    session = set_active_parent_object(session, pending.canvas_object_id)
    return replace(session, workflow=replace(session.workflow, active=False, active_primitive=""))


def _arm_child(
    session: SessionRecord,
    pending_id: str,
    request: CompoundCaptureRequest,
) -> SessionRecord:
    from metrology_process_planner.workflows.compound_capture import arm_inner_feature_capture

    return arm_inner_feature_capture(session, pending_id, request)


def _child_primitive(request: CompoundCaptureRequest) -> CanvasObjectType:
    if request.child_kind == "line":
        return CanvasObjectType.MEASUREMENT
    return CanvasObjectType.POINT
