"""Workflow commands, events, and review results."""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
from enum import Enum
from typing import Any, Optional


class WorkflowStage(str, Enum):
    """Top-level states shared by workflow controllers."""

    IDLE = "idle"
    SETUP = "setup"
    CAPTURE = "capture"
    REVIEW = "review"
    MEASUREMENT = "measurement"
    REPAIR = "repair"
    EXPORT = "export"


class UserIntent(str, Enum):
    """User decisions returned from review and blocking UI surfaces."""

    SAVE = "save"
    DISCARD = "discard"
    RETAKE = "retake"
    EXIT = "exit"
    CONTINUE = "continue"


@dataclass(frozen=True)
class WorkflowState:
    """Serializable current workflow position."""

    stage: WorkflowStage = WorkflowStage.IDLE
    active_session_id: Optional[str] = None
    active_capture_id: Optional[str] = None
    pending_messages: tuple[str, ...] = ()


@dataclass(frozen=True)
class Command:
    """A workflow command with optional structured payload data."""

    name: str
    payload: Optional[Mapping[str, Any]] = None

    def __post_init__(self) -> None:
        if self.payload is None:
            object.__setattr__(self, "payload", {})


@dataclass(frozen=True)
class Event:
    """A workflow event emitted after a state transition."""

    name: str
    payload: Optional[Mapping[str, Any]] = None

    def __post_init__(self) -> None:
        if self.payload is None:
            object.__setattr__(self, "payload", {})


@dataclass(frozen=True)
class ReviewResult:
    """Result returned by capture or measurement review UI."""

    intent: UserIntent
    label: str = ""
    notes: str = ""
    metadata: Optional[Mapping[str, Any]] = None

    def __post_init__(self) -> None:
        if self.metadata is None:
            object.__setattr__(self, "metadata", {})


@dataclass(frozen=True)
class RepairRequest:
    """Request to repair or regenerate a missing session artifact."""

    artifact_path: str
    reason: str
    preferred_action: str = "regenerate"
