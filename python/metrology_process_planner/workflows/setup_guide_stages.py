"""Setup-guide stage construction helpers."""

from __future__ import annotations

from metrology_process_planner.domains.session import (
    ModeDefinition,
    ModeRegistry,
    SessionRecord,
)
from metrology_process_planner.workflows.setup_guide_metrology_stages import (
    alignment_mark_stage,
    origin_choice_stage,
    origin_reference_stage,
)
from metrology_process_planner.workflows.setup_guide_models import (
    SetupGuideAction,
    SetupStageSnapshot,
    SetupStageStatus,
)
from metrology_process_planner.workflows.setup_guide_process_stages import recipe_stage
from metrology_process_planner.workflows.setup_guide_ready_stage import ready_stage
from metrology_process_planner.workflows.setup_guide_stage_items import (
    matching_item,
    overlay_stage_item,
    stage_from_item,
    unmatched_items,
)


def setup_stages(
    session: SessionRecord,
    mode: ModeDefinition | None,
    mode_registry: ModeRegistry | None = None,
) -> tuple[SetupStageSnapshot, ...]:
    """Return setup cards from session items, mode policy, or defaults."""

    stage_types = mode.setup.stage_types if mode is not None else ()
    if mode is not None and stage_types:
        return _mode_stages(session, stage_types, mode, mode_registry)
    if session.setup.items:
        return tuple(
            stage_from_item(item, session, mode_registry)
            for item in session.setup.items
        )
    return _default_stages(session)


def _mode_stages(
    session: SessionRecord,
    stage_types: tuple[str, ...],
    mode: ModeDefinition,
    mode_registry: ModeRegistry | None,
) -> tuple[SetupStageSnapshot, ...]:
    stages = tuple(_mode_stage(session, stage_type, mode) for stage_type in stage_types)
    merged = tuple(
        overlay_stage_item(
            stage,
            matching_item(session.setup.items, stage),
            session,
            mode_registry,
        )
        for stage in stages
    )
    extras = tuple(
        stage_from_item(item, session, mode_registry)
        for item in unmatched_items(session.setup.items, stages)
    )
    return merged + extras


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
        return recipe_stage(session)
    if stage_type == "origin_choice":
        return origin_choice_stage(session)
    if stage_type == "optional_origin_point":
        return _origin_stage(session, mode, "optional_origin_point", "Origin Point")
    if stage_type == "optional_origin_reference_image":
        return origin_reference_stage(session)
    if stage_type == "required_optical_alignment_mark":
        return alignment_mark_stage(
            session,
            "optical_alignment",
            "alignment_box_capture",
            "Optical Alignment Mark",
            "StartOpticalAlignmentCapture",
            "Start Optical Alignment Capture",
        )
    if stage_type == "required_sem_alignment_mark":
        return alignment_mark_stage(
            session,
            "sem_alignment",
            "sem_alignment_box_capture",
            "SEM Alignment Mark",
            "StartSemAlignmentCapture",
            "Start SEM Alignment Capture",
        )
    if stage_type == "ready_for_capture":
        return ready_stage(session, mode)
    return _generic_stage(stage_type, _label_for_type(stage_type), SetupStageStatus.NOT_STARTED)


def _default_stages(session: SessionRecord) -> tuple[SetupStageSnapshot, ...]:
    return (
        _generic_stage("coordinates", "Choose coordinate frame", SetupStageStatus.COMPLETE),
        _origin_stage(session, None),
        _alignment_stage(session),
        ready_stage(session),
    )


def _origin_stage(
    session: SessionRecord,
    mode: ModeDefinition | None,
    stage_id: str = "origin",
    label: str = "Capture or accept origin",
) -> SetupStageSnapshot:
    required = bool(mode and mode.setup.origin_policy == "required")
    if session.setup.origin is not None:
        status = SetupStageStatus.COMPLETE
    elif required:
        status = SetupStageStatus.ACTIVE
    else:
        status = SetupStageStatus.NOT_STARTED
    return SetupStageSnapshot(
        stage_id,
        "origin_point_capture",
        label,
        status,
        required=required,
        description="Capture an origin point when local coordinates are needed.",
        primary_action=SetupGuideAction("StartOriginPointCapture", "Start Origin Capture"),
        secondary_actions=_origin_secondary_actions(required),
    )


def _origin_secondary_actions(required: bool) -> tuple[SetupGuideAction, ...]:
    actions = [SetupGuideAction("UseGlobalCoordinates", "Use Global")]
    if not required:
        actions.append(SetupGuideAction("SkipOptionalSetupStage", "Skip"))
    return tuple(actions)
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


def _generic_stage(
    stage_type: str,
    label: str,
    status: SetupStageStatus,
) -> SetupStageSnapshot:
    return SetupStageSnapshot(stage_type, stage_type, label, status)


def _label_for_type(stage_type: str) -> str:
    return stage_type.replace("_", " ").title()
