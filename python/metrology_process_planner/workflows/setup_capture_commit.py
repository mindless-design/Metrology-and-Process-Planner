"""Commit shared canvas box captures into durable setup items."""

from __future__ import annotations

from dataclasses import dataclass, replace

from metrology_process_planner.domains.artifacts.artifact_ids import artifact_id
from metrology_process_planner.domains.geometry import Point
from metrology_process_planner.domains.session import (
    ArtifactFileMetadata,
    ArtifactOwnerRef,
    ArtifactRecord,
    ArtifactStatus,
    CanvasObject,
    CanvasObjectType,
    CanvasVisualFlag,
    CanvasWorkflowState,
    CaptureGeometry,
    OriginRecord,
    SessionRecord,
    SetupItemRecord,
)
from metrology_process_planner.workflows.canvas_interaction_models import (
    InteractionContext,
    InteractionResult,
)
from metrology_process_planner.workflows.canvas_state import (
    replace_canvas_object,
    select_canvas_object,
)


@dataclass(frozen=True)
class SetupCaptureDefinition:
    """Stable setup item and artifact metadata for one capture stage."""

    item_id: str
    item_type: str
    label: str
    artifact_role: str
    required: bool


_SETUP_CAPTURE_DEFINITIONS = {
    "origin_reference_box_capture": SetupCaptureDefinition(
        "origin_reference",
        "origin_reference_box_capture",
        "Origin Reference Image",
        "origin_reference_image",
        False,
    ),
    "alignment_box_capture": SetupCaptureDefinition(
        "optical_alignment",
        "alignment_box_capture",
        "Optical Alignment Mark",
        "optical_alignment_image",
        True,
    ),
    "sem_alignment_box_capture": SetupCaptureDefinition(
        "sem_alignment",
        "sem_alignment_box_capture",
        "SEM Alignment Mark",
        "sem_alignment_image",
        True,
    ),
}


def commit_setup_box_if_active(
    session: SessionRecord,
    context: InteractionContext,
    preview: CanvasObject,
) -> InteractionResult | None:
    """Commit a setup capture preview when the active workflow stage is setup-owned."""

    definition = _SETUP_CAPTURE_DEFINITIONS.get(session.workflow.stage)
    if definition is None:
        return None
    image_path = f"images/setup-{definition.item_id}.png"
    artifact = _setup_artifact(session, definition, image_path)
    item = _setup_item(definition, artifact.id)
    committed = replace(
        preview,
        record_id=definition.item_id,
        workflow_state=CanvasWorkflowState.SAVED,
        visual_state=(CanvasVisualFlag.SELECTED,),
    )
    artifacts = {**dict(session.artifacts or {}), artifact.id: artifact}
    session = replace_canvas_object(session, committed)
    session = replace(
        select_canvas_object(session, committed.id),
        setup=replace(session.setup, items=_upsert_setup_item(session.setup.items, item)),
        artifacts=artifacts,
        workflow=replace(
            session.workflow,
            active=False,
            stage="",
            active_primitive="",
            pending_item_ref=None,
        ),
    )
    return InteractionResult(
        session=session,
        context=replace(context, active_parent_id=committed.id, live_preview_id=None),
        artifact_requests=(image_path,),
    )


def commit_setup_origin_point_if_active(
    session: SessionRecord,
    context: InteractionContext,
    point: Point,
) -> InteractionResult | None:
    """Commit the setup origin point when the active workflow stage is origin setup."""

    if session.workflow.stage != "origin_point_capture":
        return None
    object_id = _next_canvas_id(session)
    canvas_object = CanvasObject(
        object_id,
        session.id,
        "origin",
        CanvasObjectType.POINT,
        None,
        CaptureGeometry.point_capture(point),
        CanvasWorkflowState.SAVED,
        visual_state=(CanvasVisualFlag.SELECTED,),
    )
    setup = replace(
        session.setup,
        coordinate_mode="origin",
        origin=OriginRecord(point, "origin", "origin"),
    )
    session = replace_canvas_object(replace(session, setup=setup), canvas_object)
    session = select_canvas_object(session, canvas_object.id)
    return InteractionResult(
        session=session,
        context=replace(context, active_parent_id=canvas_object.id, live_preview_id=None),
    )


def _setup_artifact(
    session: SessionRecord,
    definition: SetupCaptureDefinition,
    image_path: str,
) -> ArtifactRecord:
    return ArtifactRecord(
        artifact_id("setup", definition.item_id, definition.artifact_role),
        "image",
        definition.label,
        image_path,
        ArtifactOwnerRef("setup", definition.item_id, definition.artifact_role),
        status=ArtifactStatus.PENDING,
        file=ArtifactFileMetadata(content_type="image/png"),
        trace_ids={"session_id": session.id},
    )


def _setup_item(
    definition: SetupCaptureDefinition,
    artifact_ref: str,
) -> SetupItemRecord:
    return SetupItemRecord(
        definition.item_id,
        definition.item_type,
        definition.label,
        "complete",
        artifact_refs={"image": artifact_ref, definition.artifact_role: artifact_ref},
        metadata={"required": definition.required},
    )


def _upsert_setup_item(
    items: tuple[SetupItemRecord, ...],
    updated: SetupItemRecord,
) -> tuple[SetupItemRecord, ...]:
    remaining = tuple(item for item in items if item.id != updated.id)
    return remaining + (updated,)


def _next_canvas_id(session: SessionRecord) -> str:
    existing = {item.id for item in session.canvas_objects}
    index = 1
    while f"canvas-{index:03d}" in existing:
        index += 1
    return f"canvas-{index:03d}"
