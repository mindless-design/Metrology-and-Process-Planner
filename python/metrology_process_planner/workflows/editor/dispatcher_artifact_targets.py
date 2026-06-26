"""Artifact render target helpers for editor dispatch."""

from __future__ import annotations

from metrology_process_planner.workflows.editor.dispatcher_support import _payload_value
from metrology_process_planner.workflows.editor.document import SessionDocument
from metrology_process_planner.workflows.editor.references import RecordRef
from metrology_process_planner.workflows.editor.render_bridge_models import (
    DrawingOwnerRef,
    RenderTarget,
)
from metrology_process_planner.workflows.editor.view_models import EditorAction


def target_for_record(record_ref: RecordRef) -> RenderTarget:
    """Return the default render target for a selected record."""

    if record_ref.record_type == "measurement":
        return RenderTarget(
            DrawingOwnerRef("measurement", record_ref.record_id),
            "measurement_annotation",
        )
    return RenderTarget(DrawingOwnerRef("capture", record_ref.record_id))


def target_for_selected_artifact(
    document: SessionDocument,
    record_ref: RecordRef,
    action: EditorAction,
) -> RenderTarget | None:
    """Return a selected artifact target when it belongs to the selected item."""

    artifact_id = _payload_value(action, "artifact_id")
    if not artifact_id:
        return target_for_record(record_ref)
    artifact = (document.session.artifacts or {}).get(artifact_id)
    if artifact is None:
        return None
    owner = artifact.owner
    if owner.owner_type != record_ref.record_type or owner.owner_id != record_ref.record_id:
        return None
    return RenderTarget(
        DrawingOwnerRef(owner.owner_type, owner.owner_id),
        _render_role(owner.role),
    )


def _render_role(owner_role: str) -> str:
    for suffix in ("_spec", "_svg", "_png"):
        if owner_role.endswith(suffix):
            return owner_role[: -len(suffix)]
    return owner_role
