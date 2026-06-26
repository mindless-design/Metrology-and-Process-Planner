"""Outside-edge overview label placement and collision handling."""

from __future__ import annotations

from dataclasses import dataclass

from metrology_process_planner.domains.geometry import Box
from metrology_process_planner.rendering.overview.geometry import box_union, boxes_overlap
from metrology_process_planner.rendering.overview.layout_labels import place_labels
from metrology_process_planner.rendering.overview.leaders import LeaderRouter
from metrology_process_planner.rendering.overview.models import (
    LabelBox,
    LabelContent,
    LabelPlacementPolicy,
    LabelTarget,
    LeaderPath,
    OverviewDiagramScene,
    PlacementMetadata,
)


@dataclass(frozen=True)
class LayoutPlan:
    """Placed labels, leaders, and layout quality metadata."""

    labels: tuple[LabelBox, ...]
    leaders: tuple[LeaderPath, ...]
    metadata: PlacementMetadata
    warnings: tuple[str, ...] = ()


class OverviewLayoutPlanner:
    """Plan outside-edge labels and leaders for overview diagrams."""

    def __init__(self, router: LeaderRouter | None = None) -> None:
        self._router = router if router is not None else LeaderRouter()

    def plan(
        self,
        request_id: str,
        targets: tuple[LabelTarget, ...],
        contents: tuple[LabelContent, ...],
        policy: LabelPlacementPolicy,
        title: str = "Session Overview",
        layout_bounds: Box | None = None,
    ) -> OverviewDiagramScene:
        """Return an overview scene with placed labels and routed leaders."""

        layout = layout_bounds if layout_bounds is not None else _layout_bounds(targets)
        canvas = _canvas_size(layout, policy)
        plan = self._layout(targets, contents, layout, policy)
        return OverviewDiagramScene(
            scene_id=f"scene-{request_id}",
            title=title,
            source_image_artifact_id="",
            canvas_size=canvas,
            layout_bounds=layout,
            target_shapes=targets,
            label_boxes=plan.labels,
            leader_paths=plan.leaders,
            legend=(),
            badges=(),
            warnings=plan.warnings,
            placement_metadata=plan.metadata,
        )

    def _layout(
        self,
        targets: tuple[LabelTarget, ...],
        contents: tuple[LabelContent, ...],
        layout: Box,
        policy: LabelPlacementPolicy,
    ) -> LayoutPlan:
        content_by_target = {content.target_id: content for content in contents}
        labels = place_labels(targets, content_by_target, layout, policy)
        unresolved = _label_collision_count(labels, targets, policy)
        warnings = _placement_warnings(targets, labels, unresolved)
        leaders = self._leaders(targets, labels, policy)
        metadata = PlacementMetadata(
            policy.strategy,
            len(contents),
            len(labels),
            len(contents) - len(labels),
            max(0, len(contents) - len(labels)),
            unresolved,
            _fallback_steps(len(contents), len(labels), unresolved),
        )
        return LayoutPlan(labels, leaders, metadata, warnings)

    def _leaders(
        self,
        targets: tuple[LabelTarget, ...],
        labels: tuple[LabelBox, ...],
        policy: LabelPlacementPolicy,
    ) -> tuple[LeaderPath, ...]:
        target_by_id = {target.target_id: target for target in targets}
        label_obstacles = tuple(label.bounds for label in labels)
        target_obstacles = tuple(target.bbox for target in targets if target.priority >= 70)
        obstacles = (
            label_obstacles + target_obstacles
            if policy.avoid_target_overlap
            else label_obstacles
        )
        leaders: list[LeaderPath] = []
        for label in labels:
            target = target_by_id[label.target_id]
            leaders.append(self._router.route(target, label, obstacles, tuple(leaders)))
        return tuple(leaders)


def _layout_bounds(targets: tuple[LabelTarget, ...]) -> Box:
    return box_union(target.bbox for target in targets)


def _canvas_size(layout: Box, policy: LabelPlacementPolicy) -> tuple[int, int]:
    width = max(640, int(layout.width + policy.margin_px * 2))
    height = max(480, int(layout.height + policy.margin_px * 2))
    return (width, height)


def _label_collision_count(
    labels: tuple[LabelBox, ...],
    targets: tuple[LabelTarget, ...],
    policy: LabelPlacementPolicy,
) -> int:
    count = 0
    for index, label in enumerate(labels):
        count += sum(
            1
            for other in labels[index + 1 :]
            if boxes_overlap(label.bounds, other.bounds, policy.label_spacing_px)
        )
        count += sum(1 for target in targets if boxes_overlap(label.bounds, target.bbox))
    return count


def _placement_warnings(
    targets: tuple[LabelTarget, ...],
    labels: tuple[LabelBox, ...],
    unresolved: int,
) -> tuple[str, ...]:
    warnings: list[str] = []
    if len(labels) < len(targets):
        warnings.append("LABELS_OMITTED_DUE_TO_SPACE")
    if unresolved:
        warnings.append("LABEL_LAYOUT_COLLISION_UNRESOLVED")
    return tuple(warnings)


def _fallback_steps(
    requested: int,
    placed: int,
    unresolved: int,
) -> tuple[str, ...]:
    steps: list[str] = []
    if placed < requested:
        steps.append("omit_low_priority_labels")
    if unresolved:
        steps.append("reduce_detail_level")
    return tuple(steps)
