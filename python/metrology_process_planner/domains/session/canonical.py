"""Core canonical v5 session document support records."""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
from typing import Any, Optional

from metrology_process_planner.domains.session.constants import SESSION_SCHEMA_VERSION, utc_now_iso


@dataclass(frozen=True)
class SchemaRecord:
    """Semantic schema metadata for canonical session JSON."""

    version: str = SESSION_SCHEMA_VERSION
    previous_version: Optional[str] = None
    migrated_from: Optional[str] = None

    def to_dict(self) -> dict[str, Any]:
        """Serialize schema metadata."""

        return {
            "version": self.version,
            "previous_version": self.previous_version,
            "migrated_from": self.migrated_from,
        }

    @classmethod
    def from_dict(cls, data: Mapping[str, Any]) -> SchemaRecord:
        """Build schema metadata from saved data."""

        return cls(
            version=str(data.get("version", SESSION_SCHEMA_VERSION)),
            previous_version=_optional_str(data.get("previous_version")),
            migrated_from=_optional_str(data.get("migrated_from")),
        )


@dataclass(frozen=True)
class SessionIdentity:
    """Human-readable session identity block."""

    id: str
    name: str
    mode: str
    created_at: str
    updated_at: str

    def to_dict(self) -> dict[str, str]:
        """Serialize session identity."""

        return {
            "id": self.id,
            "name": self.name,
            "mode": self.mode,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
        }

    @classmethod
    def from_dict(cls, data: Mapping[str, Any]) -> SessionIdentity:
        """Build session identity from saved data."""

        now = utc_now_iso()
        return cls(
            id=str(data["id"]),
            name=str(data.get("name", "Untitled session")),
            mode=str(data.get("mode", "simple_capture")),
            created_at=str(data.get("created_at", now)),
            updated_at=str(data.get("updated_at", now)),
        )


@dataclass(frozen=True)
class SessionPathsRecord:
    """Portable paths associated with a session document."""

    path_mode: str = "relative_to_session_json"
    session_json: str = "session.json"
    artifact_root: str = "."
    artifacts_dir: str = "artifacts"
    csv_path: str = "exports/session_summary.csv"
    images: str = "images"
    drawings: str = "drawings"
    reports: str = "reports"
    process_outputs: str = "process_outputs"

    def to_dict(self) -> dict[str, str]:
        """Serialize paths."""

        return {
            "path_mode": self.path_mode,
            "session_json": self.session_json,
            "artifact_root": self.artifact_root,
            "artifacts_dir": self.artifacts_dir,
            "csv_path": self.csv_path,
            "images": self.images,
            "drawings": self.drawings,
            "reports": self.reports,
            "process_outputs": self.process_outputs,
        }

    @classmethod
    def from_dict(cls, data: Mapping[str, Any]) -> SessionPathsRecord:
        """Build paths from saved data."""

        return cls(
            path_mode=str(data.get("path_mode", "relative_to_session_json")),
            session_json=str(data.get("session_json", "session.json")),
            artifact_root=str(data.get("artifact_root", ".")),
            artifacts_dir=str(data.get("artifacts_dir", "artifacts")),
            csv_path=str(data.get("csv_path", "exports/session_summary.csv")),
            images=str(data.get("images", "images")),
            drawings=str(data.get("drawings", "drawings")),
            reports=str(data.get("reports", "reports")),
            process_outputs=str(data.get("process_outputs", "process_outputs")),
        )


@dataclass(frozen=True)
class SourceLayoutContext:
    """Layout file and cell context for captures."""

    layout_path: str = ""
    layout_name: str = ""
    top_cell: str = ""
    layout_fingerprint: str = ""
    klayout_version: str = ""

    def to_dict(self) -> dict[str, str]:
        """Serialize source-layout context."""

        return {
            "layout_path": self.layout_path,
            "layout_name": self.layout_name,
            "top_cell": self.top_cell,
            "layout_fingerprint": self.layout_fingerprint,
            "klayout_version": self.klayout_version,
        }

    @classmethod
    def from_dict(cls, data: Mapping[str, Any]) -> SourceLayoutContext:
        """Build source-layout context from saved data."""

        return cls(
            layout_path=str(data.get("layout_path", "")),
            layout_name=str(data.get("layout_name", "")),
            top_cell=str(data.get("top_cell", "")),
            layout_fingerprint=str(data.get("layout_fingerprint", "")),
            klayout_version=str(data.get("klayout_version", "")),
        )


@dataclass(frozen=True)
class CoordinateContext:
    """Coordinate frame metadata for saved geometry."""

    units: str = "layout"
    y_axis: str = "up"
    origin: str = "layout"
    scale: float = 1.0

    def to_dict(self) -> dict[str, Any]:
        """Serialize coordinate context."""

        return {
            "units": self.units,
            "y_axis": self.y_axis,
            "origin": self.origin,
            "scale": self.scale,
        }

    @classmethod
    def from_dict(cls, data: Mapping[str, Any]) -> CoordinateContext:
        """Build coordinate context from saved data."""

        return cls(
            units=str(data.get("units", "layout")),
            y_axis=str(data.get("y_axis", "up")),
            origin=str(data.get("origin", "layout")),
            scale=float(data.get("scale", 1.0)),
        )


def _optional_str(value: Any) -> Optional[str]:
    return None if value is None else str(value)
