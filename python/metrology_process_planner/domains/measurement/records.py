"""Measurement data models and validation."""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
from typing import Any, Optional

from metrology_process_planner.domains.geometry import Box, Point

MEASUREMENT_TYPE_OPTIONS = (
    "cd",
    "overlay",
    "pitch",
    "space",
    "width",
    "height",
    "distance",
    "other",
)

EDGE_CONVENTION_OPTIONS = (
    "outer_edges",
    "inner_edges",
    "centerline",
    "left_edge",
    "right_edge",
)


@dataclass(frozen=True)
class MeasurementRecord:
    """A line measurement nested under a parent capture."""

    id: str
    label: str
    start: Point
    end: Point
    target: Optional[float] = None
    lower_spec_limit: Optional[float] = None
    upper_spec_limit: Optional[float] = None
    notes: str = ""
    edge_detection_convention: str = ""
    annotation_color: str = "#ffcc00"
    line_weight: float = 2.0
    derived_image_names: tuple[str, ...] = ()
    artifact_refs: Optional[Mapping[str, str]] = None
    metadata: Optional[Mapping[str, Any]] = None
    warning_ids: tuple[str, ...] = ()

    def __post_init__(self) -> None:
        if self.artifact_refs is None:
            object.__setattr__(self, "artifact_refs", {})
        if self.metadata is None:
            object.__setattr__(self, "metadata", {})

    @property
    def measured_length(self) -> float:
        """Return the geometric length of the measurement line."""

        return self.start.distance_to(self.end)

    def validate_against_capture_bounds(self, bounds: Box) -> tuple[str, ...]:
        """Return warnings for a measurement within parent capture bounds."""

        warnings: list[str] = []
        if self.measured_length <= 0:
            warnings.append("Measurement line length must be greater than zero.")
        if not bounds.contains_segment(self.start, self.end):
            warnings.append("Measurement line is outside the parent capture bounds.")
        warnings.extend(self._spec_limit_warnings())
        if self.line_weight <= 0:
            warnings.append("Line weight must be positive.")
        return tuple(warnings)

    def _spec_limit_warnings(self) -> tuple[str, ...]:
        warnings: list[str] = []
        if (
            self.lower_spec_limit is not None
            and self.upper_spec_limit is not None
            and self.lower_spec_limit > self.upper_spec_limit
        ):
            warnings.append("Lower spec limit is greater than upper spec limit.")
        if (
            self.target is not None
            and self.lower_spec_limit is not None
            and self.target < self.lower_spec_limit
        ):
            warnings.append("Target is below lower spec limit.")
        if (
            self.target is not None
            and self.upper_spec_limit is not None
            and self.target > self.upper_spec_limit
        ):
            warnings.append("Target is above upper spec limit.")
        return tuple(warnings)

    def to_dict(self) -> dict[str, Any]:
        """Serialize the measurement to JSON-compatible data."""

        return {
            "id": self.id,
            "label": self.label,
            "start": self.start.to_dict(),
            "end": self.end.to_dict(),
            "measured_length": self.measured_length,
            "target": self.target,
            "lower_spec_limit": self.lower_spec_limit,
            "upper_spec_limit": self.upper_spec_limit,
            "notes": self.notes,
            "edge_detection_convention": self.edge_detection_convention,
            "annotation_color": self.annotation_color,
            "line_weight": self.line_weight,
            "derived_image_names": list(self.derived_image_names),
            "artifact_refs": dict(self.artifact_refs or {}),
            "metadata": dict(self.metadata or {}),
            "warning_ids": list(self.warning_ids),
        }

    @classmethod
    def from_dict(cls, data: Mapping[str, Any]) -> MeasurementRecord:
        """Build a measurement from saved JSON-compatible data."""

        return cls(
            id=str(data["id"]),
            label=str(data.get("label", "")),
            start=Point.from_dict(data["start"]),
            end=Point.from_dict(data["end"]),
            target=_optional_float(data.get("target")),
            lower_spec_limit=_optional_float(data.get("lower_spec_limit")),
            upper_spec_limit=_optional_float(data.get("upper_spec_limit")),
            notes=str(data.get("notes", "")),
            edge_detection_convention=str(data.get("edge_detection_convention", "")),
            annotation_color=str(data.get("annotation_color", "#ffcc00")),
            line_weight=float(data.get("line_weight", 2.0)),
            derived_image_names=tuple(str(name) for name in data.get("derived_image_names", ())),
            artifact_refs=dict(data.get("artifact_refs", {})),
            metadata=dict(data.get("metadata", {})),
            warning_ids=tuple(str(item) for item in data.get("warning_ids", ())),
        )


def _optional_float(value: Any) -> Optional[float]:
    return None if value is None else float(value)
