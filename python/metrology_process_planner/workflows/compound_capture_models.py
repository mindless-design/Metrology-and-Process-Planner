"""Typed contracts for shared compound capture workflows."""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
from typing import Any

from metrology_process_planner.domains.session import SessionRecord, WarningRecord


@dataclass(frozen=True)
class CompoundCaptureRequest:
    """Declarative request for a shared compound capture sequence."""

    mode_id: str
    sequence_type: str
    site_role: str
    child_role: str
    child_kind: str
    child_label: str = ""
    child_canvas_object_type: str = ""
    recipe_policy: str = "recommended"
    solver_operation: str = ""
    render_profile: str = ""
    annotation_role: str = ""
    process_artifact_roles: tuple[str, ...] = ()
    saved_capture_type: str = ""
    extension_key: str = ""
    feature_id_field: str = ""
    process_output_key: str = ""
    label_template: str = "Site {sequence:02d}"


@dataclass(frozen=True)
class ParentGeometryRef:
    """Reference to a pending or saved parent site geometry."""

    pending_id: str
    canvas_object_id: str


@dataclass(frozen=True)
class InnerFeatureDefinition:
    """Typed inner feature captured inside a parent site box."""

    id: str
    label: str
    role: str
    kind: str
    geometry: Mapping[str, Any]
    parent_geometry_id: str = "primary"


@dataclass(frozen=True)
class PendingCompositeCapture:
    """A pending parent plus validated inner feature awaiting editor review."""

    parent: ParentGeometryRef
    feature: InnerFeatureDefinition | None
    request: CompoundCaptureRequest


@dataclass(frozen=True)
class CompoundCaptureState:
    """Durable workflow state for a compound capture sequence."""

    request: CompoundCaptureRequest
    pending_parent_id: str = ""
    pending_child_id: str = ""
    stage: str = "parent"


@dataclass(frozen=True)
class CompositeCaptureResult:
    """Result of saving or mutating a composite capture."""

    session: SessionRecord
    capture_id: str = ""
    warnings: tuple[WarningRecord, ...] = ()


@dataclass(frozen=True)
class CompositeReviewIntent:
    """Editor intent for reviewing a pending composite capture."""

    pending_id: str
    selected_item_id: str


@dataclass(frozen=True)
class SaveCompositeCaptureCommand:
    """Save a pending composite capture with reviewed metadata."""

    pending_id: str
    label: str = ""
    notes: str = ""
    metadata: Mapping[str, Any] | None = None


@dataclass(frozen=True)
class RetakeParentCommand:
    """Discard the parent and child geometry and return to parent capture."""

    pending_id: str


@dataclass(frozen=True)
class RetakeInnerFeatureCommand:
    """Discard only the inner feature and keep the parent active."""

    pending_id: str


@dataclass(frozen=True)
class DiscardCompositeCommand:
    """Discard a pending composite capture."""

    pending_id: str


@dataclass(frozen=True)
class ExitCompositeCommand:
    """Exit compound capture mode while preserving pending review state."""

    pending_id: str
