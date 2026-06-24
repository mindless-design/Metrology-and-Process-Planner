"""Setup-guide stage construction helpers."""

from __future__ import annotations

from collections.abc import Mapping

from metrology_process_planner.domains.session import (
    ModeDefinition,
    SessionRecord,
    SetupItemRecord,
)
from metrology_process_planner.workflows.setup_guide_models import (
    SetupGuideAction,
    SetupStageSnapshot,
    SetupStageStatus,
)


def setup_stages(
    session: SessionRecord,
    mode: ModeDefinition | None,
) -> tuple[SetupStageSnapshot, ...]:
    """Return setup cards from session items, mode policy, or defaults."""

    if session.setup.items:
        return tuple(_stage_from_item(item) for item in session.setup.items)
    stage_types = mode.setup.stage_types if mode is not None else ()
    if mode is not None and stage_types:
        return tuple(_mode_stage(session, stage_type, mode) for stage_type in stage_types)
    return _default_stages(session)


def _stage_from_item(item: SetupItemRecord) -> SetupStageSnapshot:
    metadata = item.metadata or {}
    primary = _action_from_metadata(metadata, "primary_action", "primary_action_label")
    return SetupStageSnapshot(
        item.id,
        item.item_type,
        item.label or _label_for_type(item.item_type),
        _status_from_text(item.status),
        required=bool(metadata.get("required", True)),
        description=str(metadata.get("description", "")),
        primary_action=primary,
        secondary_actions=_secondary_actions(metadata),
        warning_ids=item.warning_ids,
    )


def _mode_stage(
    session: SessionRecord,
    stage_type: str,
    mode: ModeDefinition,
) -> SetupStageSnapshot:
    if stage_type == "source_layout":
        return _generic_stage(stage_type, "Source Layout", SetupStageStatus.COMPLETE)
    if stage_type == "coordinate_origin":
        return _origin_stage(session, mode)
    if stage_type == "recipe_context":
        return _recipe_stage(session)
    return _generic_stage(stage_type, _label_for_type(stage_type), SetupStageStatus.NOT_STARTED)


def _default_stages(session: SessionRecord) -> tuple[SetupStageSnapshot, ...]:
    return (
        _generic_stage("coordinates", "Choose coordinate frame", SetupStageStatus.COMPLETE),
        _origin_stage(session, None),
        _alignment_stage(session),
        _ready_stage(session),
    )


def _origin_stage(
    session: SessionRecord,
    mode: ModeDefinition | None,
) -> SetupStageSnapshot:
    required = bool(mode and mode.setup.origin_policy == "required")
    if session.setup.origin is not None:
        status = SetupStageStatus.COMPLETE
    elif required:
        status = SetupStageStatus.ACTIVE
    else:
        status = SetupStageStatus.NOT_STARTED
    return SetupStageSnapshot(
        "origin",
        "origin_point_capture",
        "Capture or accept origin",
        status,
        required=required,
        description="Capture an origin point when local coordinates are needed.",
        primary_action=SetupGuideAction("StartOriginPointCapture", "Start Origin Capture"),
        secondary_actions=(SetupGuideAction("UseGlobalCoordinates", "Use Global"),),
    )


def _alignment_stage(session: SessionRecord) -> SetupStageSnapshot:
    status = SetupStageStatus.COMPLETE if session.setup.alignments else SetupStageStatus.NOT_STARTED
    return SetupStageSnapshot(
        "alignment",
        "alignment_box_capture",
        "Capture alignment marks",
        status,
        required=False,
        description="Capture alignment marks for setup-heavy modes.",
        primary_action=SetupGuideAction("StartAlignmentCapture", "Start Alignment Capture"),
        secondary_actions=(SetupGuideAction("SkipOptionalSetupStage", "Skip"),),
    )


def _recipe_stage(session: SessionRecord) -> SetupStageSnapshot:
    has_recipe = bool(session.process_context.recipe_id or session.process_context.recipe_path)
    return SetupStageSnapshot(
        "recipe_context",
        "recipe_select",
        "Attach recipe",
        SetupStageStatus.COMPLETE if has_recipe else SetupStageStatus.WARNING,
        required=False,
        description="Attach a process recipe before process-aware outputs are generated.",
        primary_action=SetupGuideAction("AttachRecipe", "Attach Recipe"),
        secondary_actions=(SetupGuideAction("ValidateRecipeContext", "Validate"),),
        warning_ids=session.process_context.warning_ids,
    )


def _ready_stage(session: SessionRecord) -> SetupStageSnapshot:
    complete = session.setup.is_capture_ready
    return SetupStageSnapshot(
        "complete",
        "ready_for_capture",
        "Ready for capture",
        SetupStageStatus.COMPLETE if complete else SetupStageStatus.BLOCKED,
        description="Setup can be marked ready after required stages are complete.",
        primary_action=SetupGuideAction("MarkSetupComplete", "Mark Setup Complete", not complete),
    )


def _generic_stage(
    stage_type: str,
    label: str,
    status: SetupStageStatus,
) -> SetupStageSnapshot:
    return SetupStageSnapshot(stage_type, stage_type, label, status)


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
