"""Private helper functions for canvas interaction workflows."""

from __future__ import annotations

from collections.abc import Iterable, Mapping
from dataclasses import replace
from typing import Optional

from metrology_process_planner.domains.session import (
    ArtifactFileMetadata,
    ArtifactOwnerRef,
    ArtifactRecord,
    ArtifactStatus,
    CanvasObject,
    CanvasObjectType,
    CanvasVisualFlag,
    PendingCapture,
    SessionRecord,
)
from metrology_process_planner.domains.session.artifact_ids import artifact_id
from metrology_process_planner.workflows.canvas_interaction_models import InteractionContext
from metrology_process_planner.workflows.canvas_state import find_canvas_object


def box_capture_is_active(context: InteractionContext, shift_pressed: bool) -> bool:
    """Return whether a Shift box capture gesture should be handled."""

    return context.armed_object_type == CanvasObjectType.SITE_BOX and shift_pressed


def line_capture_is_active(context: InteractionContext, shift_pressed: bool) -> bool:
    """Return whether a Shift line capture gesture should be handled."""

    return context.armed_object_type == CanvasObjectType.MEASUREMENT and shift_pressed


def live_preview(
    session: SessionRecord,
    context: InteractionContext,
    shift_pressed: bool,
) -> Optional[CanvasObject]:
    """Return the current live preview object when it can be updated."""

    if not box_capture_is_active(context, shift_pressed) or context.live_preview_id is None:
        return None
    return find_canvas_object(session, context.live_preview_id)


def line_live_preview(
    session: SessionRecord,
    context: InteractionContext,
    shift_pressed: bool,
) -> Optional[CanvasObject]:
    """Return the current line preview object when it can be updated."""

    if not line_capture_is_active(context, shift_pressed) or context.live_preview_id is None:
        return None
    return find_canvas_object(session, context.live_preview_id)


def next_id(prefix: str, existing_ids: Iterable[str]) -> str:
    """Return a deterministic unused id with a numeric suffix."""

    existing = {str(item) for item in existing_ids}
    index = 1
    while f"{prefix}-{index:03d}" in existing:
        index += 1
    return f"{prefix}-{index:03d}"


def pending_by_id(session: SessionRecord, pending_id: str) -> Optional[PendingCapture]:
    """Return a pending capture by id when it exists."""

    for pending in session.pending_captures:
        if pending.id == pending_id:
            return pending
    return None


def without_pending(session: SessionRecord, pending_id: str) -> tuple[PendingCapture, ...]:
    """Return pending captures with one id removed."""

    return tuple(item for item in session.pending_captures if item.id != pending_id)


def pending_capture_artifact(
    pending: PendingCapture,
    capture_id: str,
) -> ArtifactRecord | None:
    """Return the promoted crop artifact for a saved pending capture."""

    if pending.image_artifact_path is None:
        return None
    return ArtifactRecord(
        id=artifact_id("capture", capture_id, "crop"),
        type="image",
        label="crop",
        relative_path=pending.image_artifact_path,
        owner=ArtifactOwnerRef("capture", capture_id, "crop"),
        status=ArtifactStatus.PRESENT,
        file=ArtifactFileMetadata(content_type=_content_type(pending.image_artifact_path)),
        trace_ids=pending.trace_ids,
    )


def pending_crop_artifact(pending: PendingCapture) -> ArtifactRecord | None:
    """Return the pending crop artifact owned by a pending capture."""

    if pending.image_artifact_path is None:
        return None
    return ArtifactRecord(
        id=artifact_id("pending_capture", pending.id, "pending_crop"),
        type="image",
        label="pending_crop",
        relative_path=pending.image_artifact_path,
        owner=ArtifactOwnerRef("pending_capture", pending.id, "pending_crop"),
        status=ArtifactStatus.PENDING,
        file=ArtifactFileMetadata(content_type=_content_type(pending.image_artifact_path)),
        trace_ids=pending.trace_ids,
    )


def pending_artifact_paths(pending: PendingCapture) -> tuple[str, ...]:
    """Return generated artifact paths associated with a pending capture."""

    if pending.image_artifact_path is None:
        return ()
    return (pending.image_artifact_path,)


def without_pending_artifacts(
    artifacts: Mapping[str, ArtifactRecord],
    pending_id: str,
) -> dict[str, ArtifactRecord]:
    """Return artifacts with one pending-capture owner removed."""

    return {
        artifact_id: artifact
        for artifact_id, artifact in artifacts.items()
        if not (
            artifact.owner.owner_type == "pending_capture"
            and artifact.owner.owner_id == pending_id
        )
    }


def _content_type(path: str) -> str:
    suffix = path.rsplit(".", 1)[-1].lower() if "." in path else ""
    if suffix == "png":
        return "image/png"
    if suffix in {"jpg", "jpeg"}:
        return "image/jpeg"
    if suffix == "svg":
        return "image/svg+xml"
    return ""


def with_visual_flag(canvas_object: CanvasObject, flag: CanvasVisualFlag) -> CanvasObject:
    """Return an object with the requested visual flag present."""

    if flag in canvas_object.visual_state:
        return canvas_object
    return replace(canvas_object, visual_state=canvas_object.visual_state + (flag,))
