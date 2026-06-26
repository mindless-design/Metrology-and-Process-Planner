"""Reference value objects shared by unified editor view models."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Optional


@dataclass(frozen=True)
class RecordRef:
    """Reference from an editor item to a session record."""

    record_type: str
    record_id: str
    parent_id: Optional[str] = None


@dataclass(frozen=True)
class ArtifactRef:
    """Reference from an editor item to a session artifact."""

    role: str
    path: str
    artifact_id: str = ""
    artifact_type: str = ""
    status: str = "available"
    message: str = ""
    warning_ids: tuple[str, ...] = ()
    repair_action: str = ""
    repair_suggestion: str = ""
