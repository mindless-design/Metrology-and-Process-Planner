"""Leader routing for overview callout diagrams."""

from __future__ import annotations

from metrology_process_planner.domains.geometry import Box, Point
from metrology_process_planner.rendering.overview.geometry import (
    segment_intersects_box,
    segments_intersect,
)
from metrology_process_planner.rendering.overview.models import LabelBox, LabelTarget, LeaderPath


class LeaderRouter:
    """Route simple elbow leaders between target anchors and label boxes."""

    def route(
        self,
        target: LabelTarget,
        label: LabelBox,
        obstacles: tuple[Box, ...] = (),
        existing: tuple[LeaderPath, ...] = (),
    ) -> LeaderPath:
        """Return a leader path with collision metadata."""

        start = target.anchor_point
        end = _label_edge_point(start, label.bounds)
        elbow = _elbow_point(start, end, label.bounds)
        points = (start, elbow, end) if elbow != start and elbow != end else (start, end)
        warnings = _collision_warnings(points, obstacles, existing)
        return LeaderPath(
            leader_id=f"leader-{target.target_id}-{label.label_id}",
            target_id=target.target_id,
            label_id=label.label_id,
            points=points,
            crossing_count=len(warnings),
            collision_warnings=warnings,
        )


def _label_edge_point(anchor: Point, label_box: Box) -> Point:
    box = label_box.normalized()
    candidates = (
        Point(box.left, box.center.y),
        Point(box.right, box.center.y),
        Point(box.center.x, box.bottom),
        Point(box.center.x, box.top),
    )
    return min(candidates, key=lambda point: point.distance_to(anchor))


def _elbow_point(start: Point, end: Point, label_box: Box) -> Point:
    box = label_box.normalized()
    if end.x in {box.left, box.right}:
        return Point(end.x, start.y)
    return Point(start.x, end.y)


def _collision_warnings(
    points: tuple[Point, ...],
    obstacles: tuple[Box, ...],
    existing: tuple[LeaderPath, ...],
) -> tuple[str, ...]:
    warnings: list[str] = []
    segments = tuple(zip(points, points[1:]))
    for start, end in segments:
        if any(segment_intersects_box(start, end, obstacle) for obstacle in obstacles):
            warnings.append("leader_obstacle_crossing")
            break
    if any(_segments_cross_existing(start, end, existing) for start, end in segments):
        warnings.append("leader_leader_crossing")
    return tuple(warnings)


def _segments_cross_existing(start: Point, end: Point, existing: tuple[LeaderPath, ...]) -> bool:
    for leader in existing:
        for other_start, other_end in zip(leader.points, leader.points[1:]):
            if segments_intersect(start, end, other_start, other_end):
                return True
    return False

