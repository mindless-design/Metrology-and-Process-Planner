"""Pending child-feature mutation helpers for compound capture workflows."""

from __future__ import annotations

from dataclasses import replace

from metrology_process_planner.domains.session import (
    CanvasObject,
    CanvasObjectType,
    CanvasVisualFlag,
    CanvasWorkflowState,
    PendingCapture,
    SessionRecord,
)
from metrology_process_planner.workflows.canvas_interaction_helpers import next_id
from metrology_process_planner.workflows.canvas_state import (
    replace_canvas_object,
    select_canvas_object,
    set_active_parent_object,
)
from metrology_process_planner.workflows.compound_capture_models import (
    CompoundCaptureRequest,
    InnerFeatureDefinition,
)
from metrology_process_planner.workflows.compound_capture_records import (
    compound_payload,
    feature_geometry,
    feature_payload,
)


def with_child_feature(
    session: SessionRecord,
    pending: PendingCapture,
    request: CompoundCaptureRequest,
    feature: InnerFeatureDefinition,
    object_type: CanvasObjectType,
) -> SessionRecord:
    """Return a session with a pending inner feature canvas object."""

    object_id = next_id("canvas", (item.id for item in session.canvas_objects))
    canvas = CanvasObject(
        object_id,
        session.id,
        feature.id,
        object_type,
        pending.canvas_object_id,
        feature_geometry(feature),
        CanvasWorkflowState.PENDING,
        visual_state=(CanvasVisualFlag.SELECTED,),
    )
    payload = {**compound_payload(request), "feature": feature_payload(feature)}
    session = replace_pending(session, replace(pending, metadata={"compound": payload}))
    session = replace_canvas_object(session, canvas)
    session = select_canvas_object(session, canvas.id)
    return set_active_parent_object(session, pending.canvas_object_id)


def required_pending(session: SessionRecord, pending_id: str) -> PendingCapture:
    """Return a pending capture by id or raise a validation error."""

    for pending in session.pending_captures:
        if pending.id == pending_id:
            return pending
    raise ValueError(f"Pending capture {pending_id} was not found.")


def replace_pending(session: SessionRecord, pending: PendingCapture) -> SessionRecord:
    """Return a session with one pending capture replaced."""

    return replace(
        session,
        pending_captures=tuple(
            pending if item.id == pending.id else item for item in session.pending_captures
        ),
    )


def feature_ids(session: SessionRecord) -> tuple[str, ...]:
    """Return all saved feature ids in a session."""

    return tuple(
        str(feature.get("id", ""))
        for capture in session.captures
        for feature in capture.geometry.features
    )
