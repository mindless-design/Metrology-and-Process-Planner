"""Setup-guide state-machine contracts."""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum


class SetupGuideState(str, Enum):
    """Top-level setup-guide states rendered by the modeless guide."""

    SESSION_REQUIRED = "session_required"
    COORDINATE_MODE_REQUIRED = "coordinate_mode_required"
    ORIGIN_POINT_REQUIRED = "origin_point_required"
    ORIGIN_REFERENCE_OPTIONAL = "origin_reference_optional"
    ALIGNMENT_REQUIRED = "alignment_required"
    RECIPE_REQUIRED = "recipe_required"
    RECIPE_WARNING = "recipe_warning"
    SETUP_READY = "setup_ready"
    BLOCKED = "blocked"
    FAILED = "failed"


class SetupStageStatus(str, Enum):
    """Per-card setup stage status."""

    NOT_STARTED = "not_started"
    ACTIVE = "active"
    WAITING_FOR_CANVAS_CAPTURE = "waiting_for_canvas_capture"
    PENDING_REVIEW = "pending_review"
    COMPLETE = "complete"
    SKIPPED = "skipped"
    BLOCKED = "blocked"
    WARNING = "warning"
    FAILED = "failed"


@dataclass(frozen=True)
class SetupGuideAction:
    """One command intent exposed by the setup guide."""

    command_id: str
    label: str
    enabled: bool = True
    disabled_reason: str = ""


@dataclass(frozen=True)
class SetupStageSnapshot:
    """One durable setup card derived from session and mode state."""

    stage_id: str
    stage_type: str
    label: str
    status: SetupStageStatus
    required: bool = True
    description: str = ""
    primary_action: SetupGuideAction | None = None
    secondary_actions: tuple[SetupGuideAction, ...] = ()
    warning_ids: tuple[str, ...] = ()
    requirement_badge: str = "required"
    artifact_badge: str = "none"


@dataclass(frozen=True)
class SetupGuideSnapshot:
    """Complete state-machine output for a setup guide render."""

    state: SetupGuideState
    mode_display_name: str
    active_stage_id: str
    stages: tuple[SetupStageSnapshot, ...]
    actions: tuple[SetupGuideAction, ...]
    status_message: str
