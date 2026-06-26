"""Label candidate placement helpers for overview diagrams."""

from __future__ import annotations

from metrology_process_planner.domains.geometry import Box
from metrology_process_planner.rendering.overview.geometry import boxes_overlap
from metrology_process_planner.rendering.overview.models import (
    LabelBox,
    LabelContent,
    LabelPlacementPolicy,
    LabelTarget,
)


def place_labels(
    targets: tuple[LabelTarget, ...],
    contents: dict[str, LabelContent],
    layout: Box,
    policy: LabelPlacementPolicy,
) -> tuple[LabelBox, ...]:
    """Return placed labels ordered by target priority."""

    placed: list[LabelBox] = []
    capacity = _label_capacity(layout, policy)
    for target in sorted(targets, key=lambda item: (-item.priority, item.target_id)):
        if not _is_placeable(target):
            continue
        if len(placed) >= capacity and target.priority < 70:
            continue
        content = contents.get(target.target_id)
        if content is None:
            continue
        candidate = _best_candidate(target, content, layout, policy, tuple(placed))
        if candidate is not None:
            placed.append(candidate)
    return tuple(placed)


def _is_placeable(target: LabelTarget) -> bool:
    return target.target_type != "measurement_line" or target.priority >= 65


def _best_candidate(
    target: LabelTarget,
    content: LabelContent,
    layout: Box,
    policy: LabelPlacementPolicy,
    placed: tuple[LabelBox, ...],
) -> LabelBox | None:
    for zone in _preferred_zones(target, layout, policy):
        candidate = _candidate_for_zone(target, content, layout, policy, zone, len(placed))
        if not _collides(candidate, placed, (target,), policy):
            return candidate
    if target.priority < 40:
        return None
    return _candidate_for_zone(
        target,
        _reduced_content(content),
        layout,
        policy,
        "right_margin",
        len(placed),
    )


def _preferred_zones(
    target: LabelTarget,
    layout: Box,
    policy: LabelPlacementPolicy,
) -> tuple[str, ...]:
    center = layout.center
    primary = "right_margin" if target.anchor_point.x >= center.x else "left_margin"
    secondary = "top_margin" if target.anchor_point.y >= center.y else "bottom_margin"
    ordered = (
        primary,
        secondary,
        "right_margin",
        "left_margin",
        "top_margin",
        "bottom_margin",
    )
    return tuple(zone for zone in ordered if zone in policy.allowed_zones)


def _candidate_for_zone(
    target: LabelTarget,
    content: LabelContent,
    layout: Box,
    policy: LabelPlacementPolicy,
    zone: str,
    index: int,
) -> LabelBox:
    lines = _content_lines(content)
    width = min(content.max_width_px, max(content.min_width_px, _text_width(lines)))
    height = 24 + 16 * (len(lines) - 1)
    offset = index * (height + policy.label_spacing_px)
    bounds = _zone_bounds(layout, policy, zone, width, height, offset)
    return LabelBox(
        content.label_id,
        target.target_id,
        lines,
        bounds,
        target.style_hint,
        content.priority,
    )


def _zone_bounds(
    layout: Box,
    policy: LabelPlacementPolicy,
    zone: str,
    width: int,
    height: int,
    offset: int,
) -> Box:
    if zone == "left_margin":
        return Box(
            layout.left - policy.margin_px,
            layout.top - height - offset,
            layout.left - 8,
            layout.top - offset,
        )
    if zone == "top_margin":
        return Box(
            layout.left + offset,
            layout.top + 8,
            layout.left + offset + width,
            layout.top + 8 + height,
        )
    if zone == "bottom_margin":
        return Box(
            layout.left + offset,
            layout.bottom - height - 8,
            layout.left + offset + width,
            layout.bottom - 8,
        )
    return Box(
        layout.right + 8,
        layout.top - height - offset,
        layout.right + 8 + width,
        layout.top - offset,
    )


def _content_lines(content: LabelContent) -> tuple[str, ...]:
    return tuple(
        line for line in (content.title, content.subtitle, *content.detail_lines) if line
    )


def _text_width(lines: tuple[str, ...]) -> int:
    return max((len(line) * 7 + 20 for line in lines), default=72)


def _label_capacity(layout: Box, policy: LabelPlacementPolicy) -> int:
    lane_height = 34
    vertical = int(max(layout.height + policy.margin_px * 2, lane_height) // lane_height)
    horizontal_lanes = min(6, int(max(layout.width, lane_height) // lane_height))
    return max(4, vertical * 2 + horizontal_lanes)


def _collides(
    candidate: LabelBox,
    placed: tuple[LabelBox, ...],
    targets: tuple[LabelTarget, ...],
    policy: LabelPlacementPolicy,
) -> bool:
    label_hit = policy.avoid_label_overlap and any(
        boxes_overlap(candidate.bounds, label.bounds, policy.label_spacing_px)
        for label in placed
    )
    target_hit = policy.avoid_target_overlap and any(
        boxes_overlap(candidate.bounds, target.bbox, policy.label_spacing_px)
        for target in targets
    )
    return label_hit or target_hit


def _reduced_content(content: LabelContent) -> LabelContent:
    return LabelContent(
        content.label_id,
        content.target_id,
        content.title,
        priority=content.priority,
        max_width_px=content.max_width_px,
        min_width_px=content.min_width_px,
    )
