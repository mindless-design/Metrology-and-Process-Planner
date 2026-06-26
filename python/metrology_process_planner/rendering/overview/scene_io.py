"""JSON-compatible serialization for overview scenes."""

from __future__ import annotations

from typing import Any

from metrology_process_planner.domains.geometry import Box, Point
from metrology_process_planner.rendering.overview.models import (
    LabelBox,
    LabelTarget,
    LeaderPath,
    OverviewDiagramScene,
)


def scene_to_dict(scene: OverviewDiagramScene) -> dict[str, Any]:
    """Serialize an overview scene for artifact metadata and diagnostics."""

    return {
        "scene_id": scene.scene_id,
        "title": scene.title,
        "source_image_artifact_id": scene.source_image_artifact_id,
        "canvas_size": list(scene.canvas_size),
        "layout_bounds": scene.layout_bounds.to_dict(),
        "target_shapes": [_target_to_dict(item) for item in scene.target_shapes],
        "label_boxes": [_label_to_dict(item) for item in scene.label_boxes],
        "leader_paths": [_leader_to_dict(item) for item in scene.leader_paths],
        "legend": list(scene.legend),
        "badges": list(scene.badges),
        "scale_bar": dict(scene.scale_bar or {}),
        "warnings": list(scene.warnings),
        "placement_metadata": scene.placement_metadata.__dict__,
    }


def _target_to_dict(target: LabelTarget) -> dict[str, Any]:
    return {
        "target_id": target.target_id,
        "target_type": target.target_type,
        "source_item_id": target.source_item_id,
        "geometry": dict(target.geometry),
        "anchor_point": target.anchor_point.to_dict(),
        "bbox": target.bbox.to_dict(),
        "priority": target.priority,
        "label_role": target.label_role,
        "status": target.status,
        "warning_ids": list(target.warning_ids),
        "style_hint": target.style_hint,
        "metadata": dict(target.metadata or {}),
    }


def _label_to_dict(label: LabelBox) -> dict[str, Any]:
    return {
        "label_id": label.label_id,
        "target_id": label.target_id,
        "text_lines": list(label.text_lines),
        "bounds": label.bounds.to_dict(),
        "style": label.style,
        "priority": label.priority,
        "detail_level": label.detail_level,
        "status": label.status,
    }


def _leader_to_dict(leader: LeaderPath) -> dict[str, Any]:
    return {
        "leader_id": leader.leader_id,
        "target_id": leader.target_id,
        "label_id": leader.label_id,
        "points": [point.to_dict() for point in leader.points],
        "style": leader.style,
        "crossing_count": leader.crossing_count,
        "collision_warnings": list(leader.collision_warnings),
    }


def point_from_dict(data: dict[str, Any]) -> Point:
    """Build a point from scene JSON."""

    return Point.from_dict(data)


def box_from_dict(data: dict[str, Any]) -> Box:
    """Build a box from scene JSON."""

    return Box.from_dict(data)

