"""Workflow resume and audit session records."""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
from typing import Any, Optional

from metrology_process_planner.domains.session.constants import utc_now_iso


@dataclass(frozen=True)
class WorkflowState:
    """Minimal durable resume state for workflow restart."""

    active: bool = False
    stage: str = ""
    active_mode: str = ""
    active_primitive: str = ""
    pending_item_ref: Optional[str] = None
    next_id_counters: Optional[Mapping[str, int]] = None
    incomplete_artifact_tasks: tuple[str, ...] = ()
    last_saved_capture_id: Optional[str] = None

    def __post_init__(self) -> None:
        if self.next_id_counters is None:
            object.__setattr__(self, "next_id_counters", {})

    def to_dict(self) -> dict[str, Any]:
        """Serialize durable workflow state."""

        return {
            "active": self.active,
            "stage": self.stage,
            "active_mode": self.active_mode,
            "active_primitive": self.active_primitive,
            "pending_item_ref": self.pending_item_ref,
            "next_id_counters": dict(self.next_id_counters or {}),
            "incomplete_artifact_tasks": list(self.incomplete_artifact_tasks),
            "last_saved_capture_id": self.last_saved_capture_id,
        }

    @classmethod
    def from_dict(cls, data: Mapping[str, Any]) -> WorkflowState:
        """Build durable workflow state from saved data."""

        counters = {
            str(key): int(value)
            for key, value in dict(data.get("next_id_counters", {})).items()
        }
        return cls(
            active=bool(data.get("active", False)),
            stage=str(data.get("stage", "")),
            active_mode=str(data.get("active_mode", "")),
            active_primitive=str(data.get("active_primitive", "")),
            pending_item_ref=_optional_str(data.get("pending_item_ref")),
            next_id_counters=counters,
            incomplete_artifact_tasks=tuple(
                str(item) for item in data.get("incomplete_artifact_tasks", ())
            ),
            last_saved_capture_id=_optional_str(data.get("last_saved_capture_id")),
        )


@dataclass(frozen=True)
class AuditEvent:
    """Append-only audit event stored in canonical session JSON."""

    id: str
    event_type: str
    message: str
    created_at: str = ""
    source: str = "session"
    details: Optional[Mapping[str, Any]] = None

    def __post_init__(self) -> None:
        if not self.created_at:
            object.__setattr__(self, "created_at", utc_now_iso())
        if self.details is None:
            object.__setattr__(self, "details", {})

    def to_dict(self) -> dict[str, Any]:
        """Serialize audit event."""

        return {
            "id": self.id,
            "event_type": self.event_type,
            "message": self.message,
            "created_at": self.created_at,
            "source": self.source,
            "details": dict(self.details or {}),
        }

    @classmethod
    def from_dict(cls, data: Mapping[str, Any]) -> AuditEvent:
        """Build audit event from saved data."""

        return cls(
            id=str(data["id"]),
            event_type=str(data.get("event_type", "")),
            message=str(data.get("message", "")),
            created_at=str(data.get("created_at", "")),
            source=str(data.get("source", "session")),
            details=dict(data.get("details", {})),
        )


def _optional_str(value: Any) -> Optional[str]:
    return None if value is None else str(value)
