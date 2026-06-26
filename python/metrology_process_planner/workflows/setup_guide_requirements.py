"""Required setup-stage checks shared by guide views and commands."""

from __future__ import annotations

from metrology_process_planner.domains.session import ModeDefinition, SessionRecord

_REQUIRED_SETUP_STAGES = {
    "origin_choice": ("Coordinate Mode", "", ""),
    "required_optical_alignment_mark": (
        "Optical Alignment Mark",
        "optical_alignment",
        "alignment_box_capture",
    ),
    "required_sem_alignment_mark": (
        "SEM Alignment Mark",
        "sem_alignment",
        "sem_alignment_box_capture",
    ),
}


def incomplete_required_setup_labels(
    session: SessionRecord,
    mode: ModeDefinition,
) -> tuple[str, ...]:
    """Return required setup labels that are not complete for a mode."""

    missing: list[str] = []
    for stage_type in mode.setup.stage_types:
        if _stage_incomplete(session, stage_type):
            missing.append(_REQUIRED_SETUP_STAGES[stage_type][0])
    return tuple(missing)


def _stage_incomplete(session: SessionRecord, stage_type: str) -> bool:
    if stage_type not in _REQUIRED_SETUP_STAGES:
        return False
    if stage_type == "origin_choice":
        return not bool(session.setup.coordinate_mode)
    _label, item_id, item_type = _REQUIRED_SETUP_STAGES[stage_type]
    return not setup_item_complete(session, item_id, item_type)


def setup_item_complete(
    session: SessionRecord,
    item_id: str,
    item_type: str,
) -> bool:
    """Return whether a setup item is complete by stable id or item type."""

    return any(
        item.status == "complete" and (item.id == item_id or item.item_type == item_type)
        for item in session.setup.items
    )
