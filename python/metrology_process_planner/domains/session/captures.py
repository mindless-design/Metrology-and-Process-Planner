"""Capture records and nested measurement data."""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass, replace
from typing import Any, Optional

from metrology_process_planner.domains.measurements import MeasurementRecord
from metrology_process_planner.domains.session.capture_geometry import CaptureGeometry
from metrology_process_planner.domains.session.constants import utc_now_iso


@dataclass(frozen=True)
class CaptureRecord:
    """A reviewed layout capture and its nested measurement records."""

    id: str
    label: str
    geometry: CaptureGeometry
    created_at: str
    sequence: int = 0
    role: str = "site"
    type: str = "layout_region"
    status: str = "saved"
    modified_at: str = ""
    notes: str = ""
    artifact_refs: Optional[Mapping[str, str]] = None
    metadata: Optional[Mapping[str, Any]] = None
    annotations: Optional[Mapping[str, Any]] = None
    children: tuple[str, ...] = ()
    extensions: Optional[Mapping[str, Any]] = None
    warning_ids: tuple[str, ...] = ()
    measurements: tuple[MeasurementRecord, ...] = ()
    trace_ids: Optional[Mapping[str, str]] = None

    def __post_init__(self) -> None:
        if not self.modified_at:
            object.__setattr__(self, "modified_at", self.created_at)
        if self.artifact_refs is None:
            object.__setattr__(self, "artifact_refs", {})
        if self.metadata is None:
            object.__setattr__(self, "metadata", {})
        if self.annotations is None:
            object.__setattr__(self, "annotations", {})
        if self.extensions is None:
            object.__setattr__(self, "extensions", {})
        if self.trace_ids is None:
            object.__setattr__(self, "trace_ids", {})

    def validation_warnings(self) -> tuple[str, ...]:
        """Return warnings for geometry and nested measurements."""

        warnings = list(self.geometry.validate())
        if self.geometry.bounds is not None:
            for measurement in self.measurements:
                warnings.extend(measurement.validate_against_capture_bounds(self.geometry.bounds))
        return tuple(warnings)

    def add_measurement(self, measurement: MeasurementRecord) -> CaptureRecord:
        """Return a copy of this capture with an added measurement."""

        return replace(self, measurements=self.measurements + (measurement,))

    def to_dict(self) -> dict[str, Any]:
        """Serialize the capture to JSON-compatible data."""

        return {
            "id": self.id,
            "sequence": self.sequence,
            "label": self.label,
            "role": self.role,
            "type": self.type,
            "status": self.status,
            "geometry": self.geometry.to_dict(),
            "created_at": self.created_at,
            "modified_at": self.modified_at,
            "notes": self.notes,
            "artifact_refs": dict(self.artifact_refs or {}),
            "metadata": dict(self.metadata or {}),
            "annotations": dict(self.annotations or {}),
            "children": list(self.children),
            "extensions": dict(self.extensions or {}),
            "warning_ids": list(self.warning_ids),
            "measurements": [measurement.to_dict() for measurement in self.measurements],
            "trace_ids": dict(self.trace_ids or {}),
        }

    @classmethod
    def from_dict(cls, data: Mapping[str, Any]) -> CaptureRecord:
        """Build a capture from saved JSON-compatible data."""

        return cls(
            id=str(data["id"]),
            sequence=int(data.get("sequence", 0)),
            label=str(data.get("label", "")),
            geometry=CaptureGeometry.from_dict(data["geometry"]),
            created_at=str(data.get("created_at", utc_now_iso())),
            modified_at=str(data.get("modified_at", data.get("created_at", ""))),
            role=str(data.get("role", "site")),
            type=str(data.get("type", "layout_region")),
            status=str(data.get("status", "saved")),
            notes=str(data.get("notes", "")),
            artifact_refs=dict(data.get("artifact_refs", {})),
            metadata=dict(data.get("metadata", {})),
            annotations=dict(data.get("annotations", {})),
            children=tuple(str(item) for item in data.get("children", ())),
            extensions=dict(data.get("extensions", {})),
            warning_ids=tuple(str(item) for item in data.get("warning_ids", ())),
            measurements=tuple(
                MeasurementRecord.from_dict(item) for item in data.get("measurements", ())
            ),
            trace_ids=dict(data.get("trace_ids", {})),
        )
