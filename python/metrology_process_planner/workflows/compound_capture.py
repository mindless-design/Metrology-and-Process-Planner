"""Shared compound site-then-feature capture workflow operations."""

from __future__ import annotations

from dataclasses import replace

from metrology_process_planner.domains.session import (
    CanvasObjectType,
    SessionRecord,
    WorkflowState,
    utc_now_iso,
)
from metrology_process_planner.workflows.canvas_interaction_helpers import next_id, without_pending
from metrology_process_planner.workflows.canvas_state import set_active_parent_object
from metrology_process_planner.workflows.compound_capture_features import (
    add_line_feature,
    add_point_feature,
)
from metrology_process_planner.workflows.compound_capture_models import (
    CompositeCaptureResult,
    CompoundCaptureRequest,
    InnerFeatureDefinition,
    PendingCompositeCapture,
    SaveCompositeCaptureCommand,
)
from metrology_process_planner.workflows.compound_capture_pending import (
    replace_pending,
    required_pending,
)
from metrology_process_planner.workflows.compound_capture_records import (
    capture_from_composite,
    compound_payload,
    pending_composite_from_pending,
    saved_canvas_objects,
)
from metrology_process_planner.workflows.compound_capture_requests import (
    ellipsometry_request,
    profilometry_request,
)
from metrology_process_planner.workflows.compound_capture_support import (
    composite_artifacts,
    process_output,
    process_warnings,
)
from metrology_process_planner.workflows.compound_capture_validation import (
    composite_save_warnings,
)

__all__ = [
    "CompoundCaptureRequest",
    "CompositeCaptureResult",
    "InnerFeatureDefinition",
    "PendingCompositeCapture",
    "SaveCompositeCaptureCommand",
    "add_line_feature",
    "add_point_feature",
    "arm_inner_feature_capture",
    "begin_compound_capture",
    "ellipsometry_request",
    "pending_composite_from_pending",
    "profilometry_request",
    "save_composite_capture",
]


def begin_compound_capture(
    session: SessionRecord,
    request: CompoundCaptureRequest,
) -> SessionRecord:
    """Arm the parent site box step for a compound capture."""

    return replace(
        session,
        workflow=replace(
            session.workflow,
            active=True,
            stage=f"{request.sequence_type}:parent",
            active_mode=request.mode_id,
            active_primitive=CanvasObjectType.SITE_BOX.value,
        ),
    )


def arm_inner_feature_capture(
    session: SessionRecord,
    pending_id: str,
    request: CompoundCaptureRequest,
) -> SessionRecord:
    """Mark a pending parent active and arm the requested child primitive."""

    pending = required_pending(session, pending_id)
    primitive = (
        CanvasObjectType.MEASUREMENT
        if request.child_kind == "line"
        else CanvasObjectType.POINT
    )
    pending = replace(
        pending,
        metadata={**dict(pending.metadata or {}), "compound": compound_payload(request)},
    )
    session = replace_pending(session, pending)
    session = set_active_parent_object(session, pending.canvas_object_id)
    return replace(
        session,
        workflow=replace(
            session.workflow,
            active=True,
            stage=f"{request.sequence_type}:child",
            active_mode=request.mode_id,
            active_primitive=primitive.value,
            pending_item_ref=pending.id,
        ),
    )


def save_composite_capture(
    session: SessionRecord,
    command: SaveCompositeCaptureCommand,
) -> CompositeCaptureResult:
    """Promote a pending composite capture into a saved composite capture."""

    pending = required_pending(session, command.pending_id)
    composite = pending_composite_from_pending(pending)
    validation_warnings = composite_save_warnings(session, composite, command.metadata or {})
    if validation_warnings:
        raise ValueError("; ".join(validation_warnings))
    feature = composite.feature
    assert feature is not None
    capture_id = next_id("cap", (capture.id for capture in session.captures))
    warnings = process_warnings(session, capture_id, composite.request)
    warning_ids = tuple(warning.id for warning in warnings)
    artifacts = composite_artifacts(capture_id, pending.image_artifact_path, composite, warning_ids)
    capture = capture_from_composite(
        capture_id,
        pending,
        composite,
        command,
        artifacts,
        warning_ids,
    )
    session = replace(
        session,
        captures=session.captures + (capture,),
        pending_captures=without_pending(session, pending.id),
        canvas_objects=saved_canvas_objects(session, pending, capture_id, feature.id),
        artifacts={**dict(session.artifacts or {}), **{item.id: item for item in artifacts}},
        process_outputs=session.process_outputs
        + (process_output(capture_id, composite, artifacts, warning_ids),),
        warnings=session.warnings + warnings,
        workflow=WorkflowState(last_saved_capture_id=capture_id),
        updated_at=utc_now_iso(),
    )
    return CompositeCaptureResult(session, capture_id, warnings)
