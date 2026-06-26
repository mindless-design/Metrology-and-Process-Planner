"""Setup-guide helpers for persisted setup item cards."""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import replace

from metrology_process_planner.domains.modes.mode_registry import ModeRegistry
from metrology_process_planner.domains.session import SessionRecord, SetupItemRecord
from metrology_process_planner.domains.warnings.warning_visibility import (
    warning_visible_for_session,
)
from metrology_process_planner.workflows.setup_guide_artifacts import artifact_badge
from metrology_process_planner.workflows.setup_guide_models import (
    SetupGuideAction,
    SetupStageSnapshot,
    SetupStageStatus,
)
from metrology_process_planner.workflows.setup_guide_workflow_status import (
    overlay_workflow_status,
)


def stage_from_item(
    item: SetupItemRecord,
    session: SessionRecord,
    mode_registry: ModeRegistry | None = None,
) -> SetupStageSnapshot:
    """Return a generic setup card from a persisted setup item."""

    metadata = item.metadata or {}
    primary = _action_from_metadata(metadata, "primary_action", "primary_action_label")
    required = bool(metadata.get("required", True))
    return SetupStageSnapshot(
        item.id,
        item.item_type,
        item.label or _label_for_type(item.item_type),
        _status_from_text(item.status),
        required=required,
        description=str(metadata.get("description", "")),
        primary_action=primary,
        secondary_actions=_secondary_actions(metadata),
        warning_ids=_visible_warning_ids(item, session, mode_registry),
        requirement_badge=_requirement_badge(required),
        artifact_badge=artifact_badge(
            item.artifact_refs,
            session.artifacts,
            session,
            mode_registry,
        ),
    )


def overlay_stage_item(
    stage: SetupStageSnapshot,
    item: SetupItemRecord | None,
    session: SessionRecord,
    mode_registry: ModeRegistry | None = None,
) -> SetupStageSnapshot:
    """Merge durable item state into a declarative mode setup card."""

    if item is None:
        return overlay_workflow_status(stage, session)
    item_stage = stage_from_item(item, session, mode_registry)
    return overlay_workflow_status(replace(
        stage,
        status=item_stage.status,
        label=item.label or stage.label,
        description=item_stage.description or stage.description,
        primary_action=item_stage.primary_action or stage.primary_action,
        secondary_actions=item_stage.secondary_actions or stage.secondary_actions,
        warning_ids=item_stage.warning_ids,
        artifact_badge=item_stage.artifact_badge,
    ), session)


def matching_item(
    items: tuple[SetupItemRecord, ...],
    stage: SetupStageSnapshot,
) -> SetupItemRecord | None:
    """Return the persisted item that describes a declarative setup stage."""

    for item in items:
        if item.id == stage.stage_id or item.item_type == stage.stage_type:
            return item
    return None


def unmatched_items(
    items: tuple[SetupItemRecord, ...],
    stages: tuple[SetupStageSnapshot, ...],
) -> tuple[SetupItemRecord, ...]:
    """Return persisted setup items not covered by declarative stage cards."""

    covered_ids = {stage.stage_id for stage in stages}
    covered_types = {stage.stage_type for stage in stages}
    return tuple(
        item for item in items if item.id not in covered_ids and item.item_type not in covered_types
    )


def _requirement_badge(required: bool) -> str:
    return "required" if required else "optional"


def _visible_warning_ids(
    item: SetupItemRecord,
    session: SessionRecord,
    mode_registry: ModeRegistry | None,
) -> tuple[str, ...]:
    warnings = {warning.id: warning for warning in session.warnings}
    return tuple(
        warning_id
        for warning_id in item.warning_ids
        if warning_id not in warnings
        or warning_visible_for_session(session, warnings[warning_id], mode_registry)
    )


def _status_from_text(value: str) -> SetupStageStatus:
    normalized = value.strip().lower()
    for status in SetupStageStatus:
        if status.value == normalized:
            return status
    if normalized in {"ready", "done"}:
        return SetupStageStatus.COMPLETE
    if normalized in {"pending", ""}:
        return SetupStageStatus.NOT_STARTED
    return SetupStageStatus.ACTIVE


def _action_from_metadata(
    metadata: Mapping[str, object],
    command_key: str,
    label_key: str,
) -> SetupGuideAction | None:
    command_id = str(metadata.get(command_key, ""))
    if not command_id:
        return None
    return SetupGuideAction(
        command_id,
        str(metadata.get(label_key, command_id)),
        bool(metadata.get(f"{command_key}_enabled", True)),
        str(metadata.get(f"{command_key}_disabled_reason", "")),
    )


def _secondary_actions(metadata: Mapping[str, object]) -> tuple[SetupGuideAction, ...]:
    raw = metadata.get("secondary_actions", ())
    if not isinstance(raw, (list, tuple)):
        return ()
    return tuple(_secondary_action(item) for item in raw)


def _secondary_action(item: object) -> SetupGuideAction:
    if isinstance(item, Mapping):
        command_id = str(item.get("command_id", item.get("id", "")))
        return SetupGuideAction(
            command_id,
            str(item.get("label", command_id)),
            bool(item.get("enabled", True)),
            str(item.get("disabled_reason", "")),
        )
    return SetupGuideAction(str(item), str(item))


def _label_for_type(stage_type: str) -> str:
    return stage_type.replace("_", " ").title()
