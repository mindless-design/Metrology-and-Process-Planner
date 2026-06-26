"""Artifact repair request models."""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum


class RepairType(str, Enum):
    """Supported artifact repair command types."""

    REGENERATE_ARTIFACT = "regenerate_artifact"
    REGENERATE_ALL_MISSING = "regenerate_all_missing"
    REGENERATE_ALL_STALE = "regenerate_all_stale"
    RELINK_ARTIFACT = "relink_artifact"
    REPLACE_CAPTURE = "replace_capture"
    REPLACE_MEASUREMENT = "replace_measurement"
    REATTACH_RECIPE = "reattach_recipe"
    REOPEN_SOURCE_LAYOUT = "reopen_source_layout"
    MARK_INTENTIONALLY_IGNORED = "mark_intentionally_ignored"
    DELETE_SUPERSEDED_ARTIFACT = "delete_superseded_artifact"
    REBUILD_CSV = "rebuild_csv"
    REBUILD_REPORT = "rebuild_report"


class RepairRequestStatus(str, Enum):
    """Repair request routing status."""

    AVAILABLE = "available"
    UNAVAILABLE = "unavailable"
    BLOCKED = "blocked"
    COMPLETED = "completed"
    FAILED = "failed"


@dataclass(frozen=True)
class RepairRequest:
    """Structured repair request surfaced to editor and diagnostics layers."""

    repair_id: str
    artifact_id: str
    repair_type: RepairType
    owner_ref: str
    requirements: tuple[str, ...]
    status: RepairRequestStatus
    user_message: str
    technical_details: str = ""
