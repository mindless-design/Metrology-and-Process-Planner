"""Top-level saved session record."""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass, replace
from enum import Enum
from typing import Any, Optional, cast

from metrology_process_planner.domains.artifacts.artifact_registry import ArtifactRecord
from metrology_process_planner.domains.capture.canvas import CanvasObject, PendingCapture
from metrology_process_planner.domains.capture.captures import CaptureRecord
from metrology_process_planner.domains.capture.grids import GridDatasetRecord
from metrology_process_planner.domains.session.canonical import (
    CoordinateContext,
    SchemaRecord,
    SessionPathsRecord,
    SourceLayoutContext,
)
from metrology_process_planner.domains.session.constants import SESSION_SCHEMA_VERSION, utc_now_iso
from metrology_process_planner.domains.session.process_outputs import (
    ProcessContext,
    ProcessOutputRecord,
    ReportRecord,
)
from metrology_process_planner.domains.session.setup import SetupState
from metrology_process_planner.domains.session.workflow import AuditEvent, WorkflowState
from metrology_process_planner.domains.warnings.warnings import WarningRecord


class SessionMode(str, Enum):
    """Declarative workflow families supported by a saved session."""

    SIMPLE_CAPTURE = "simple_capture"
    SIMPLE_LABELED_CAPTURE = "simple_labeled_capture"
    FAST_BATCH_CAPTURE = "fast_batch_capture"
    CAD_REVIEW = "cad_review"
    CAD_REVIEW_CAPTURE = "cad_review_capture"
    OPTICAL_METROLOGY = "optical_metrology"
    CDSEM_CAPTURE = "cdsem_capture"
    CDSEM_MEASUREMENT = "cdsem_measurement"
    CDSEM_PLANNING = "cdsem_planning"
    GRID_MEASUREMENT = "grid_measurement"
    PROCESS_AWARE_METROLOGY = "process_aware_metrology"
    PROCESS_FLOW_SUMMARY = "process_flow_summary"
    PROFILOMETRY_PLANNER = "profilometry_planner"
    ELLIPSOMETRY_PLANNER = "ellipsometry_planner"


class SessionModeId(str):
    """Open session mode id for externally registered declarative modes."""

    @property
    def value(self) -> str:
        """Return the mode id string."""

        return str(self)


def session_mode_id(value: str | SessionMode | SessionModeId) -> SessionMode | SessionModeId:
    """Return a built-in mode enum or open external mode id."""

    if isinstance(value, SessionMode):
        return value
    try:
        return SessionMode(str(value))
    except ValueError:
        return SessionModeId(str(value))


def session_mode_value(mode: str | SessionMode | SessionModeId) -> str:
    """Return the durable session mode id string."""

    return mode.value if hasattr(mode, "value") else str(mode)


@dataclass(frozen=True)
class SessionRecord:
    """Canonical saved session data for capture, review, repair, and export."""

    id: str
    name: str
    mode: SessionMode | SessionModeId
    created_at: str
    updated_at: str
    schema_version: str = SESSION_SCHEMA_VERSION
    schema: SchemaRecord = SchemaRecord()
    paths: SessionPathsRecord = SessionPathsRecord()
    source_layout: SourceLayoutContext = SourceLayoutContext()
    coordinates: CoordinateContext = CoordinateContext()
    setup: SetupState = SetupState()
    captures: tuple[CaptureRecord, ...] = ()
    canvas_objects: tuple[CanvasObject, ...] = ()
    pending_captures: tuple[PendingCapture, ...] = ()
    grid_datasets: tuple[GridDatasetRecord, ...] = ()
    process_context: ProcessContext = ProcessContext()
    process_outputs: tuple[ProcessOutputRecord, ...] = ()
    reports: tuple[ReportRecord, ...] = ()
    artifacts: Optional[Mapping[str, ArtifactRecord]] = None
    warnings: tuple[WarningRecord, ...] = ()
    workflow: WorkflowState = WorkflowState()
    metadata: Optional[Mapping[str, Any]] = None
    extensions: Optional[Mapping[str, Any]] = None
    audit: tuple[AuditEvent, ...] = ()

    def __post_init__(self) -> None:
        if self.metadata is None:
            object.__setattr__(self, "metadata", {})
        if self.extensions is None:
            object.__setattr__(self, "extensions", {})
        if self.schema_version != self.schema.version:
            object.__setattr__(self, "schema_version", self.schema.version)
        if self.artifacts is None:
            object.__setattr__(self, "artifacts", {})

    def add_capture(self, capture: CaptureRecord) -> SessionRecord:
        """Return a copy of this session with a capture appended."""

        return replace(self, captures=self.captures + (capture,), updated_at=utc_now_iso())

    def validation_warnings(self) -> tuple[str, ...]:
        """Return session-level and capture-level warnings."""

        warnings: list[str] = []
        capture_ids: set[str] = set()
        for capture in self.captures:
            if capture.id in capture_ids:
                warnings.append(f"Duplicate capture id: {capture.id}")
            capture_ids.add(capture.id)
            warnings.extend(f"{capture.id}: {message}" for message in capture.validation_warnings())
        return tuple(warnings)

    def to_dict(self) -> dict[str, Any]:
        """Serialize the session to JSON-compatible data."""

        from metrology_process_planner.domains.session.serialization import session_to_dict

        return session_to_dict(self)

    @classmethod
    def from_dict(
        cls,
        data: Mapping[str, Any],
        allowed_mode_ids: tuple[str, ...] = (),
    ) -> SessionRecord:
        """Build a session from saved JSON-compatible data."""

        from metrology_process_planner.domains.session.serialization import session_from_dict

        return cast(SessionRecord, session_from_dict(cls, SessionMode, data, allowed_mode_ids))
