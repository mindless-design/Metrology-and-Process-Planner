"""Structured warning records attached to canonical sessions."""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
from typing import Any, Optional

from metrology_process_planner.domains.session.constants import utc_now_iso


@dataclass(frozen=True)
class WarningRecord:
    """A user-visible issue that can be surfaced and repaired later."""

    id: str
    message: str
    severity: str = "warning"
    artifact_path: Optional[str] = None
    source: str = ""
    code: str = ""
    related_item_refs: tuple[str, ...] = ()
    related_artifact_refs: tuple[str, ...] = ()
    technical_details: str = ""
    repair_suggestion: str = ""
    status: str = "open"
    created_at: str = ""
    resolved_at: Optional[str] = None

    def __post_init__(self) -> None:
        if not self.created_at:
            object.__setattr__(self, "created_at", utc_now_iso())

    def to_dict(self) -> dict[str, Any]:
        """Serialize the warning to JSON-compatible data."""

        return {
            "id": self.id,
            "severity": self.severity,
            "source": self.source,
            "code": self.code,
            "related_item_refs": list(self.related_item_refs),
            "related_artifact_refs": list(self.related_artifact_refs),
            "message": self.message,
            "technical_details": self.technical_details,
            "repair_suggestion": self.repair_suggestion,
            "status": self.status,
            "created_at": self.created_at,
            "resolved_at": self.resolved_at,
            "artifact_path": self.artifact_path,
        }

    @classmethod
    def from_dict(cls, data: Mapping[str, Any]) -> WarningRecord:
        """Build a warning from saved JSON-compatible data."""

        return cls(
            id=str(data["id"]),
            message=str(data["message"]),
            severity=str(data.get("severity", "warning")),
            artifact_path=_optional_str(data.get("artifact_path")),
            source=str(data.get("source", "")),
            code=str(data.get("code", "")),
            related_item_refs=tuple(str(item) for item in data.get("related_item_refs", ())),
            related_artifact_refs=tuple(
                str(item) for item in data.get("related_artifact_refs", ())
            ),
            technical_details=str(data.get("technical_details", "")),
            repair_suggestion=str(data.get("repair_suggestion", "")),
            status=str(data.get("status", "open")),
            created_at=str(data.get("created_at", "")),
            resolved_at=_optional_str(data.get("resolved_at")),
        )


def _optional_str(value: Any) -> Optional[str]:
    return None if value is None else str(value)
