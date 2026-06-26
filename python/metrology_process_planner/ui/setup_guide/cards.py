"""Setup-guide card models for production shells."""

from __future__ import annotations

from dataclasses import dataclass

from metrology_process_planner.ui.shell import SetupGuideViewModel, SetupStageViewModel


@dataclass(frozen=True)
class SetupStageCardModel:
    """Display-ready setup stage card consumed by host UI shells."""

    stage_id: str
    title: str
    description: str
    status_label: str
    status_tone: str
    requirement_label: str
    artifact_label: str
    warning_label: str
    primary_action_label: str
    secondary_action_labels: tuple[str, ...] = ()
    disabled_reason: str = ""
    active: bool = False


def setup_stage_cards(view_model: SetupGuideViewModel) -> tuple[SetupStageCardModel, ...]:
    """Return card models for every setup-guide stage."""

    return tuple(_card(stage, stage.stage_id == view_model.active_stage_id)
                 for stage in view_model.stages)


def _card(stage: SetupStageViewModel, active: bool) -> SetupStageCardModel:
    return SetupStageCardModel(
        stage.stage_id,
        stage.label,
        stage.description,
        _status_label(stage.status),
        _status_tone(stage.status),
        _requirement_label(stage.requirement_badge, stage.required),
        _artifact_label(stage.artifact_badge),
        _warning_label(stage.warning_count),
        stage.next_action,
        _secondary_labels(stage),
        stage.disabled_reason,
        active,
    )


def _status_label(status: str) -> str:
    return status.replace("_", " ").title()


def _status_tone(status: str) -> str:
    return {
        "active": "accent",
        "waiting_for_canvas_capture": "accent",
        "pending_review": "accent",
        "complete": "success",
        "skipped": "muted",
        "blocked": "danger",
        "warning": "warning",
        "failed": "danger",
    }.get(status, "neutral")


def _requirement_label(badge: str, required: bool) -> str:
    value = badge or ("required" if required else "optional")
    return value.replace("_", " ").title()


def _artifact_label(badge: str) -> str:
    if not badge or badge == "none":
        return "No Artifact"
    return "Artifact: " + badge.replace("_", " ").title()


def _warning_label(count: int) -> str:
    if count == 1:
        return "1 Warning"
    if count > 1:
        return f"{count} Warnings"
    return "No Warnings"


def _secondary_labels(stage: SetupStageViewModel) -> tuple[str, ...]:
    if stage.secondary_action_views:
        return tuple(action.label for action in stage.secondary_action_views)
    return stage.secondary_actions
