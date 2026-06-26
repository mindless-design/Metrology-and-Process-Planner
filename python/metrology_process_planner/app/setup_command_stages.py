"""Setup command helpers for active-stage decisions."""

from __future__ import annotations

from dataclasses import replace

from metrology_process_planner.app.command_types import CommandBlockedError
from metrology_process_planner.domains.session import (
    ModeRegistry,
    SessionRecord,
    SetupItemRecord,
    built_in_mode_registry,
)
from metrology_process_planner.workflows.setup_guide_models import SetupStageSnapshot


def skip_optional_item(
    items: tuple[SetupItemRecord, ...],
    active: SetupStageSnapshot,
) -> tuple[SetupItemRecord, ...]:
    """Return setup items with the active optional item skipped."""

    updated: list[SetupItemRecord] = []
    skipped = False
    for item in items:
        if (
            not skipped
            and _matches_stage(item, active)
            and not _is_required(item)
            and item.status not in {"complete", "skipped"}
        ):
            updated.append(replace(item, status="skipped"))
            skipped = True
        else:
            updated.append(item)
    return tuple(updated)


def active_optional_skip_item(active: SetupStageSnapshot) -> SetupItemRecord:
    """Return a skipped setup item for the current optional stage."""

    return SetupItemRecord(
        active.stage_id,
        active.stage_type,
        active.label,
        "skipped",
        metadata={"required": active.required},
    )


def ensure_active_stage_is_optional(
    session: SessionRecord,
    mode_registry: ModeRegistry | None = None,
) -> SetupStageSnapshot:
    """Block skip routing when the active setup stage is required."""

    active = active_setup_stage(session, mode_registry)
    if active.required:
        raise CommandBlockedError(
            f"{active.label} is required and cannot be skipped.",
            "Complete the required setup card before continuing.",
        )
    return active


def incomplete_required_setup_labels(
    session: SessionRecord,
    mode_registry: ModeRegistry | None = None,
) -> tuple[str, ...]:
    """Return labels for required setup stages that are not complete."""

    from metrology_process_planner.workflows.setup_guide_requirements import (
        incomplete_required_setup_labels as incomplete_labels,
    )

    mode = (mode_registry or built_in_mode_registry()).definition(session.mode.value)
    return incomplete_labels(session, mode)


def active_setup_stage(
    session: SessionRecord,
    mode_registry: ModeRegistry | None = None,
) -> SetupStageSnapshot:
    """Return the currently active setup stage snapshot."""

    from metrology_process_planner.workflows.setup_guide_state import SetupGuideStateMachine

    mode = (mode_registry or built_in_mode_registry()).definition(session.mode.value)
    snapshot = SetupGuideStateMachine().evaluate(session, mode)
    return next(stage for stage in snapshot.stages if stage.stage_id == snapshot.active_stage_id)


def _is_required(item: SetupItemRecord) -> bool:
    return bool(dict(item.metadata or {}).get("required", True))


def _matches_stage(item: SetupItemRecord, stage: SetupStageSnapshot) -> bool:
    return item.id == stage.stage_id or item.item_type == stage.stage_type
