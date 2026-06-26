"""Capture-scoped overview helper functions."""

from __future__ import annotations

from dataclasses import replace

from metrology_process_planner.domains.geometry import Box
from metrology_process_planner.domains.session import SessionRecord
from metrology_process_planner.rendering.overview.content import build_label_content
from metrology_process_planner.rendering.overview.extraction import extract_label_targets
from metrology_process_planner.rendering.overview.layout import OverviewLayoutPlanner
from metrology_process_planner.rendering.overview.models import (
    LabelContent,
    LabelPlacementPolicy,
    LabelTarget,
    OverviewStylePolicy,
)
from metrology_process_planner.rendering.overview.renderer import OverviewDiagramRenderer
from metrology_process_planner.rendering.visual_labels import LabelSpec


def render_site_overview_svg(
    session: SessionRecord,
    capture_id: str,
    region: Box,
    label: LabelSpec,
    scene_id: str,
) -> tuple[str, tuple[int, int]]:
    """Return capture-scoped overview SVG text and canvas size."""

    targets = site_overview_targets(session, capture_id, region)
    contents = site_overview_contents(targets, capture_id, label)
    scene = OverviewLayoutPlanner().plan(
        scene_id,
        targets,
        contents,
        LabelPlacementPolicy(
            strategy="outside_edge_callouts",
            margin_px=96,
            fallback_strategy="legend_only",
        ),
        "Site Overview",
        layout_bounds=region,
    )
    svg_text = OverviewDiagramRenderer().render_svg(
        scene,
        OverviewStylePolicy(selected_target_style="#dc2626"),
    )
    return svg_text, scene.canvas_size


def expanded_bounds(bounds: Box, factor: float) -> Box:
    """Return bounds expanded around the original center."""

    box = bounds.normalized()
    pad_x = max(box.width * (factor - 1.0) / 2.0, 10.0)
    pad_y = max(box.height * (factor - 1.0) / 2.0, 10.0)
    return Box(box.left - pad_x, box.bottom - pad_y, box.right + pad_x, box.top + pad_y)


def site_overview_targets(
    session: SessionRecord,
    capture_id: str,
    region: Box,
) -> tuple[LabelTarget, ...]:
    """Return label targets relevant to one capture overview region."""

    selected = []
    for target in extract_label_targets(session):
        if target.source_item_id == capture_id or _boxes_touch(region, target.bbox):
            selected.append(_selected_target(target, capture_id))
    return tuple(selected)


def site_overview_contents(
    targets: tuple[LabelTarget, ...],
    capture_id: str,
    label: LabelSpec,
) -> tuple[LabelContent, ...]:
    """Return overview label content with full text for the selected capture."""

    contents = []
    for content in build_label_content(targets, "standard"):
        target = _target_for_content(targets, content.target_id)
        if target is not None and target.source_item_id == capture_id:
            contents.append(_selected_content(content, label))
        else:
            contents.append(content)
    return tuple(contents)


def _selected_target(target: LabelTarget, capture_id: str) -> LabelTarget:
    if target.source_item_id != capture_id:
        return target
    return replace(target, priority=95)


def _target_for_content(
    targets: tuple[LabelTarget, ...],
    target_id: str,
) -> LabelTarget | None:
    return next((item for item in targets if item.target_id == target_id), None)


def _selected_content(content: LabelContent, label: LabelSpec) -> LabelContent:
    lines = label.text_lines
    return LabelContent(
        content.label_id,
        content.target_id,
        lines[0],
        lines[1] if len(lines) > 1 else "",
        lines[2:],
        content.badges,
        content.severity,
        content.metadata_fields,
        content.max_width_px,
        content.min_width_px,
        95,
    )


def _boxes_touch(a: Box, b: Box) -> bool:
    left = max(a.left, b.left)
    right = min(a.right, b.right)
    bottom = max(a.bottom, b.bottom)
    top = min(a.top, b.top)
    return left <= right and bottom <= top
