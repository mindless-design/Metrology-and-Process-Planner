"""Grid dataset records for measurement workflows."""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
from typing import Any, Optional

from metrology_process_planner.domains.measurement.records import MeasurementRecord


@dataclass(frozen=True)
class GridDatasetRecord:
    """A logical grouping of captures used for grid measurement workflows."""

    id: str
    label: str
    capture_ids: tuple[str, ...] = ()
    measurements: tuple[MeasurementRecord, ...] = ()
    artifact_refs: Optional[Mapping[str, str]] = None
    status: str = "ready"
    metadata: Optional[Mapping[str, Any]] = None
    extensions: Optional[Mapping[str, Any]] = None
    warning_ids: tuple[str, ...] = ()

    def __post_init__(self) -> None:
        if self.artifact_refs is None:
            object.__setattr__(self, "artifact_refs", {})
        if self.metadata is None:
            object.__setattr__(self, "metadata", {})
        if self.extensions is None:
            object.__setattr__(self, "extensions", {})

    def to_dict(self) -> dict[str, Any]:
        """Serialize the grid dataset to JSON-compatible data."""

        return {
            "id": self.id,
            "label": self.label,
            "capture_ids": list(self.capture_ids),
            "measurements": [measurement.to_dict() for measurement in self.measurements],
            "artifact_refs": dict(self.artifact_refs or {}),
            "status": self.status,
            "metadata": dict(self.metadata or {}),
            "extensions": dict(self.extensions or {}),
            "warning_ids": list(self.warning_ids),
        }

    @classmethod
    def from_dict(cls, data: Mapping[str, Any]) -> GridDatasetRecord:
        """Build a grid dataset from saved JSON-compatible data."""

        return cls(
            id=str(data["id"]),
            label=str(data.get("label", "")),
            capture_ids=tuple(str(item) for item in data.get("capture_ids", ())),
            measurements=tuple(
                MeasurementRecord.from_dict(item) for item in data.get("measurements", ())
            ),
            artifact_refs=dict(data.get("artifact_refs", {})),
            status=str(data.get("status", "ready")),
            metadata=dict(data.get("metadata", {})),
            extensions=dict(data.get("extensions", {})),
            warning_ids=tuple(str(item) for item in data.get("warning_ids", ())),
        )
