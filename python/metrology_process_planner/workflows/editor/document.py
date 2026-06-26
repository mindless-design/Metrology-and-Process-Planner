"""Normalized document and item tree models for the unified session editor."""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
from enum import Enum
from pathlib import Path
from typing import Any, Optional

from metrology_process_planner.domains.session import SessionRecord
from metrology_process_planner.workflows.editor.references import ArtifactRef, RecordRef
from metrology_process_planner.workflows.editor.view_models import (
    ArtifactDetailViewModel,
    ArtifactHealthViewModel,
    WarningViewModel,
)


class SessionItemKind(str, Enum):
    """Kinds of objects visible in the generic session editor."""

    DASHBOARD = "dashboard"
    SETUP = "setup"
    PENDING_CAPTURE = "pending_capture"
    SAVED_CAPTURE = "saved_capture"
    FEATURE = "feature"
    MEASUREMENT = "measurement"
    GRID_DATASET = "grid_dataset"
    OVERVIEW = "overview"
    CROSS_SECTION = "cross_section"
    REPORT = "report"
    WARNING = "warning"


@dataclass(frozen=True)
class SessionItem:
    """One normalized object in the editor tree."""

    item_id: str
    kind: SessionItemKind
    label: str
    role: str
    status: str = "ready"
    parent_id: Optional[str] = None
    child_ids: tuple[str, ...] = ()
    record_ref: Optional[RecordRef] = None
    canvas_object_ids: tuple[str, ...] = ()
    artifact_refs: tuple[ArtifactRef, ...] = ()
    warning_ids: tuple[str, ...] = ()


@dataclass(frozen=True)
class SessionItemGroup:
    """Navigator group containing editor item ids."""

    group_id: str
    label: str
    item_ids: tuple[str, ...]


@dataclass(frozen=True)
class DirtyState:
    """Unsaved editor changes tracked outside canonical session JSON."""

    is_dirty: bool = False
    dirty_item_ids: tuple[str, ...] = ()
    unsaved_metadata_edits: tuple[tuple[str, str, str], ...] = ()
    unsaved_pending_capture: bool = False
    last_saved_revision: int = 0


@dataclass(frozen=True)
class EditorSelectionState:
    """Current editor selection and canvas object correspondence."""

    selected_item_id: str = "dashboard"
    selected_canvas_object_ids: tuple[str, ...] = ()


@dataclass(frozen=True)
class SessionDocument:
    """Normalized editor document wrapping a canonical session record."""

    session: SessionRecord
    raw_payload: Mapping[str, Any]
    items_by_id: Mapping[str, SessionItem]
    root_item_ids: tuple[str, ...]
    navigator_groups: tuple[SessionItemGroup, ...]
    selection: EditorSelectionState = EditorSelectionState()
    dirty_state: DirtyState = DirtyState()
    warning_view_models: tuple[WarningViewModel, ...] = ()
    artifact_health: ArtifactHealthViewModel = ArtifactHealthViewModel()
    artifact_details_by_item_id: Optional[Mapping[str, tuple[ArtifactDetailViewModel, ...]]] = None
    pending_capture_item_id: Optional[str] = None
    canvas_object_to_item_id: Optional[Mapping[str, str]] = None
    loaded_path: Optional[Path] = None
    revision: int = 0

    def __post_init__(self) -> None:
        if self.canvas_object_to_item_id is None:
            mapping: dict[str, str] = {}
            for item_id, item in self.items_by_id.items():
                for canvas_object_id in item.canvas_object_ids:
                    mapping[canvas_object_id] = item_id
            object.__setattr__(self, "canvas_object_to_item_id", mapping)
        if self.artifact_details_by_item_id is None:
            object.__setattr__(self, "artifact_details_by_item_id", {})

    @property
    def schema_version(self) -> str:
        """Return the loaded session JSON schema version."""

        return self.session.schema.version

    @property
    def captures(self) -> tuple[Any, ...]:
        """Return saved captures from the canonical session record."""

        return self.session.captures

    @property
    def artifacts(self) -> Mapping[str, Any]:
        """Return the central artifact registry from the session JSON."""

        return self.session.artifacts or {}

    @property
    def warnings(self) -> tuple[Any, ...]:
        """Return persisted warning records."""

        return self.session.warnings

    @property
    def workflow(self) -> Any:
        """Return persisted workflow resume state."""

        return self.session.workflow
