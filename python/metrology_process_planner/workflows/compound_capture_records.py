"""Record and canvas builders for compound capture workflows."""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import replace
from typing import Any

from metrology_process_planner.domains.geometry import Box, Point
from metrology_process_planner.domains.session import (
    ArtifactRecord,
    CanvasObject,
    CanvasWorkflowState,
    CaptureGeometry,
    CaptureRecord,
    GeometryKind,
    PendingCapture,
    SessionRecord,
)
from metrology_process_planner.workflows.compound_capture_models import (
    CompoundCaptureRequest,
    InnerFeatureDefinition,
    ParentGeometryRef,
    PendingCompositeCapture,
    SaveCompositeCaptureCommand,
)


def capture_from_composite(
    capture_id: str,
    pending: PendingCapture,
    composite: PendingCompositeCapture,
    command: SaveCompositeCaptureCommand,
    artifacts: tuple[ArtifactRecord, ...],
    warning_ids: tuple[str, ...],
) -> CaptureRecord:
    """Build a saved capture record from pending composite data."""

    request = composite.request
    feature = composite.feature
    assert feature is not None
    artifact_refs = {artifact.owner.role: artifact.id for artifact in artifacts}
    extension = _process_extension(request, feature, artifact_refs, warning_ids)
    return CaptureRecord(
        capture_id,
        command.label or default_label(request, capture_id),
        CaptureGeometry(
            kind=GeometryKind.COMPOSITE,
            bounds=required_bounds(pending),
            features=(feature_payload(feature),),
            metadata={"primary_geometry_id": "primary"},
        ),
        pending.created_at,
        role=request.site_role,
        type=request.saved_capture_type,
        notes=command.notes,
        artifact_refs=artifact_refs,
        metadata=dict(command.metadata or {}),
        extensions={request.extension_key: extension},
        warning_ids=warning_ids,
        trace_ids=pending.trace_ids,
    )


def pending_composite_from_pending(pending: PendingCapture) -> PendingCompositeCapture:
    """Return typed composite data stored on a pending capture."""

    payload = dict((pending.metadata or {}).get("compound", {}))
    request = CompoundCaptureRequest(
        str(payload.get("mode_id", "")),
        str(payload.get("sequence_type", "")),
        str(payload.get("site_role", "")),
        str(payload.get("child_role", "")),
        str(payload.get("child_kind", "")),
        str(payload.get("child_label", "")),
        str(payload.get("child_canvas_object_type", "")),
        str(payload.get("recipe_policy", "recommended")),
        str(payload.get("solver_operation", "")),
        str(payload.get("render_profile", "")),
        str(payload.get("annotation_role", "")),
        _string_tuple(payload.get("process_artifact_roles", ())),
        str(payload.get("saved_capture_type", "")),
        str(payload.get("extension_key", "")),
        str(payload.get("feature_id_field", "")),
        str(payload.get("process_output_key", "")),
        str(payload.get("label_template", "Site {sequence:02d}")),
    )
    feature = feature_from_payload(payload.get("feature"))
    parent = ParentGeometryRef(pending.id, pending.canvas_object_id)
    return PendingCompositeCapture(parent, feature, request)


def feature_from_payload(value: object) -> InnerFeatureDefinition | None:
    """Return an inner feature from pending metadata."""

    if not isinstance(value, Mapping):
        return None
    return InnerFeatureDefinition(
        str(value.get("id", "")),
        str(value.get("label", "")),
        str(value.get("role", "")),
        str(value.get("kind", "")),
        dict(value.get("geometry", {})),
        str(value.get("parent_geometry_id", "primary")),
    )


def feature_payload(feature: InnerFeatureDefinition) -> dict[str, Any]:
    """Return JSON-compatible inner feature payload."""

    return {
        "id": feature.id,
        "label": feature.label or feature.role.replace("_", " ").title(),
        "role": feature.role,
        "kind": feature.kind,
        "parent_geometry_id": feature.parent_geometry_id,
        "geometry": dict(feature.geometry),
    }


def feature_geometry(feature: InnerFeatureDefinition) -> CaptureGeometry:
    """Return canvas geometry for an inner feature."""

    geometry = dict(feature.geometry)
    if feature.kind == "line":
        return CaptureGeometry.line(
            Point.from_dict(geometry["start"]),
            Point.from_dict(geometry["end"]),
        )
    return CaptureGeometry.point_capture(Point.from_dict(geometry["point"]))


def _process_extension(
    request: CompoundCaptureRequest,
    feature: InnerFeatureDefinition,
    artifact_refs: Mapping[str, str],
    warning_ids: tuple[str, ...],
) -> dict[str, Any]:
    payload: dict[str, Any] = {
        request.feature_id_field: feature.id,
        "process_context_ref": "process_context.active",
        "solver_request": {
            "operation": request.solver_operation,
            "process_window_variant": "target",
            "render_profile": request.render_profile,
        },
        "solver_result_id": None,
        "artifact_refs": dict(artifact_refs),
        "warning_ids": list(warning_ids),
    }
    if request.process_output_key == "outputs":
        payload["outputs"] = {"stack_change_windows": [], "step_heights": []}
    else:
        payload[request.process_output_key] = []
    return payload


def _string_tuple(value: object) -> tuple[str, ...]:
    if isinstance(value, str):
        return (value,)
    if isinstance(value, (list, tuple)):
        return tuple(str(item) for item in value)
    return ()


def saved_canvas_objects(
    session: SessionRecord,
    pending: PendingCapture,
    capture_id: str,
    feature_id: str,
) -> tuple[CanvasObject, ...]:
    """Return canvas objects with parent and child promoted to saved state."""

    return tuple(
        replace(item, record_id=capture_id, workflow_state=CanvasWorkflowState.SAVED)
        if item.id == pending.canvas_object_id
        else replace(item, record_id=feature_id, workflow_state=CanvasWorkflowState.SAVED)
        if item.parent_id == pending.canvas_object_id
        else item
        for item in session.canvas_objects
    )


def compound_payload(request: CompoundCaptureRequest) -> dict[str, Any]:
    """Return JSON-compatible pending compound metadata."""

    return {
        "mode_id": request.mode_id,
        "sequence_type": request.sequence_type,
        "site_role": request.site_role,
        "child_role": request.child_role,
        "child_kind": request.child_kind,
        "child_label": request.child_label,
        "child_canvas_object_type": request.child_canvas_object_type,
        "recipe_policy": request.recipe_policy,
        "solver_operation": request.solver_operation,
        "render_profile": request.render_profile,
        "annotation_role": request.annotation_role,
        "process_artifact_roles": list(request.process_artifact_roles),
        "saved_capture_type": request.saved_capture_type,
        "extension_key": request.extension_key,
        "feature_id_field": request.feature_id_field,
        "process_output_key": request.process_output_key,
        "label_template": request.label_template,
    }


def required_bounds(pending: PendingCapture) -> Box:
    """Return parent bounds or raise a user-facing validation error."""

    if pending.geometry.bounds is None:
        raise ValueError("Compound capture parent must be a site box.")
    return pending.geometry.bounds


def default_label(request: CompoundCaptureRequest, capture_id: str) -> str:
    """Return a default label for a saved composite capture."""
    sequence = capture_id.rsplit("-", 1)[-1]
    return request.label_template.format(sequence=int(sequence) if sequence.isdigit() else sequence)
