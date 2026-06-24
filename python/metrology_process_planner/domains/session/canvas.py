"""Persistent canvas object records for interactive layout overlays."""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
from enum import Enum
from typing import Any, Optional

from metrology_process_planner.domains.session.capture_geometry import CaptureGeometry
from metrology_process_planner.domains.session.constants import utc_now_iso


class CanvasObjectType(str, Enum):
    """Durable interactive object families shown on the layout canvas."""

    SITE_BOX = "site_box"
    POINT = "point"
    LINE = "line"
    MEASUREMENT = "measurement"
    PROFILOMETRY_LINE = "profilometry_line"
    ELLIPSOMETRY_POINT = "ellipsometry_point"
    CROSS_SECTION = "cross_section"
    PROFILOMETRY = "profilometry"
    FIB_CUT = "fib_cut"
    MULTI_LINE = "multi_line"


class CanvasWorkflowState(str, Enum):
    """Lifecycle state for a persistent canvas object."""

    LIVE_PREVIEW = "live_preview"
    PENDING = "pending"
    SAVED = "saved"
    SUPERSEDED = "superseded"


class CanvasVisualFlag(str, Enum):
    """Independent visual flags used by overlay and editor surfaces."""

    SELECTED = "selected"
    ACTIVE_PARENT = "active_parent"
    STALE = "stale"
    INVALID = "invalid"
    HIDDEN = "hidden"


@dataclass(frozen=True)
class SourceViewBinding:
    """Reference to the layout view context that produced a canvas object."""

    layout_name: str = ""
    cell_name: str = ""
    view_id: str = ""

    def to_dict(self) -> dict[str, str]:
        """Serialize source view binding metadata."""

        return {
            "layout_name": self.layout_name,
            "cell_name": self.cell_name,
            "view_id": self.view_id,
        }

    @classmethod
    def from_dict(cls, data: Mapping[str, Any]) -> SourceViewBinding:
        """Build source view binding metadata from saved data."""

        return cls(
            layout_name=str(data.get("layout_name", "")),
            cell_name=str(data.get("cell_name", "")),
            view_id=str(data.get("view_id", "")),
        )


@dataclass(frozen=True)
class CanvasObject:
    """A selectable persistent visual proxy for a saved or pending record."""

    id: str
    session_id: str
    record_id: str
    object_type: CanvasObjectType
    parent_id: Optional[str]
    geometry: CaptureGeometry
    workflow_state: CanvasWorkflowState
    source_view_binding: SourceViewBinding = SourceViewBinding()
    visual_state: tuple[CanvasVisualFlag, ...] = ()
    selectable: bool = True
    visible: bool = True
    locked: bool = False
    stale: bool = False
    warning_ids: tuple[str, ...] = ()
    trace_ids: Optional[Mapping[str, str]] = None

    def __post_init__(self) -> None:
        if self.trace_ids is None:
            object.__setattr__(self, "trace_ids", {})

    def to_dict(self) -> dict[str, Any]:
        """Serialize canvas object metadata to JSON-compatible data."""

        return {
            "id": self.id,
            "session_id": self.session_id,
            "record_id": self.record_id,
            "object_type": self.object_type.value,
            "parent_id": self.parent_id,
            "geometry": self.geometry.to_dict(),
            "workflow_state": self.workflow_state.value,
            "source_view_binding": self.source_view_binding.to_dict(),
            "visual_state": [flag.value for flag in self.visual_state],
            "selectable": self.selectable,
            "visible": self.visible,
            "locked": self.locked,
            "stale": self.stale,
            "warning_ids": list(self.warning_ids),
            "trace_ids": dict(self.trace_ids or {}),
        }

    @classmethod
    def from_dict(cls, data: Mapping[str, Any]) -> CanvasObject:
        """Build canvas object metadata from saved JSON-compatible data."""

        return cls(
            id=str(data["id"]),
            session_id=str(data["session_id"]),
            record_id=str(data["record_id"]),
            object_type=CanvasObjectType(str(data["object_type"])),
            parent_id=_optional_str(data.get("parent_id")),
            geometry=CaptureGeometry.from_dict(data["geometry"]),
            workflow_state=CanvasWorkflowState(str(data["workflow_state"])),
            source_view_binding=SourceViewBinding.from_dict(
                data.get("source_view_binding", {})
            ),
            visual_state=tuple(
                CanvasVisualFlag(str(flag)) for flag in data.get("visual_state", ())
            ),
            selectable=bool(data.get("selectable", True)),
            visible=bool(data.get("visible", True)),
            locked=bool(data.get("locked", False)),
            stale=bool(data.get("stale", False)),
            warning_ids=tuple(str(item) for item in data.get("warning_ids", ())),
            trace_ids=dict(data.get("trace_ids", {})),
        )


@dataclass(frozen=True)
class PendingCapture:
    """A capture awaiting review before becoming a saved capture record."""

    id: str
    session_id: str
    canvas_object_id: str
    object_type: CanvasObjectType
    geometry: CaptureGeometry
    parent_id: Optional[str] = None
    created_at: str = ""
    image_artifact_path: Optional[str] = None
    source_view_binding: SourceViewBinding = SourceViewBinding()
    metadata: Optional[Mapping[str, Any]] = None
    trace_ids: Optional[Mapping[str, str]] = None

    def __post_init__(self) -> None:
        if not self.created_at:
            object.__setattr__(self, "created_at", utc_now_iso())
        if self.metadata is None:
            object.__setattr__(self, "metadata", {})
        if self.trace_ids is None:
            object.__setattr__(self, "trace_ids", {})

    def to_dict(self) -> dict[str, Any]:
        """Serialize pending capture metadata to JSON-compatible data."""

        return {
            "id": self.id,
            "session_id": self.session_id,
            "canvas_object_id": self.canvas_object_id,
            "object_type": self.object_type.value,
            "geometry": self.geometry.to_dict(),
            "parent_id": self.parent_id,
            "created_at": self.created_at,
            "image_artifact_path": self.image_artifact_path,
            "source_view_binding": self.source_view_binding.to_dict(),
            "metadata": dict(self.metadata or {}),
            "trace_ids": dict(self.trace_ids or {}),
        }

    @classmethod
    def from_dict(cls, data: Mapping[str, Any]) -> PendingCapture:
        """Build pending capture metadata from saved JSON-compatible data."""

        return cls(
            id=str(data["id"]),
            session_id=str(data["session_id"]),
            canvas_object_id=str(data["canvas_object_id"]),
            object_type=CanvasObjectType(str(data["object_type"])),
            geometry=CaptureGeometry.from_dict(data["geometry"]),
            parent_id=_optional_str(data.get("parent_id")),
            created_at=str(data.get("created_at", "")),
            image_artifact_path=_optional_str(data.get("image_artifact_path")),
            source_view_binding=SourceViewBinding.from_dict(
                data.get("source_view_binding", {})
            ),
            metadata=dict(data.get("metadata", {})),
            trace_ids=dict(data.get("trace_ids", {})),
        )


def _optional_str(value: Any) -> Optional[str]:
    return None if value is None else str(value)
