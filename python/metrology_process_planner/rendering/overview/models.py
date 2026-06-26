"""Overview diagram request, label, layout, and scene models."""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
from typing import Any, Optional

from metrology_process_planner.domains.geometry import Box, Point


@dataclass(frozen=True)
class OverviewDiagramRequest:
    """Input contract for generating one reusable overview diagram artifact."""

    request_id: str
    session_id: str
    source_layout_ref: str = ""
    region_of_interest: str = "capture_collection_bbox"
    included_item_ids: tuple[str, ...] = ("all_captures", "measurements", "user_labels")
    excluded_item_ids: tuple[str, ...] = ("hidden_captures", "superseded_captures")
    label_policy: Mapping[str, Any] | None = None
    placement_policy: LabelPlacementPolicy | None = None
    leader_policy: Mapping[str, Any] | None = None
    style_policy: OverviewStylePolicy | None = None
    output_spec: Mapping[str, Any] | None = None
    artifact_role: str = "session_overview"


@dataclass(frozen=True)
class UserLabelRecord:
    """Durable arbitrary user label stored in session JSON extensions."""

    label_id: str
    geometry: Mapping[str, Any]
    title: str
    notes: str = ""
    style: str = "user_note"
    created_at: str = ""
    modified_at: str = ""
    artifact_refs: tuple[str, ...] = ()
    warning_ids: tuple[str, ...] = ()
    include_in_overview: bool = True
    hidden: bool = False
    priority: int = 50

    def to_dict(self) -> dict[str, Any]:
        """Serialize the label to session extension JSON."""

        return {
            "label_id": self.label_id,
            "geometry": dict(self.geometry),
            "title": self.title,
            "notes": self.notes,
            "style": self.style,
            "created_at": self.created_at,
            "modified_at": self.modified_at,
            "artifact_refs": list(self.artifact_refs),
            "warning_ids": list(self.warning_ids),
            "include_in_overview": self.include_in_overview,
            "hidden": self.hidden,
            "priority": self.priority,
        }

    @classmethod
    def from_dict(cls, data: Mapping[str, Any]) -> UserLabelRecord:
        """Build a user label from extension JSON."""

        return cls(
            label_id=str(data["label_id"]),
            geometry=dict(data.get("geometry", {})),
            title=str(data.get("title", "")),
            notes=str(data.get("notes", "")),
            style=str(data.get("style", "user_note")),
            created_at=str(data.get("created_at", "")),
            modified_at=str(data.get("modified_at", "")),
            artifact_refs=tuple(str(item) for item in data.get("artifact_refs", ())),
            warning_ids=tuple(str(item) for item in data.get("warning_ids", ())),
            include_in_overview=bool(data.get("include_in_overview", True)),
            hidden=bool(data.get("hidden", False)),
            priority=int(data.get("priority", 50)),
        )


@dataclass(frozen=True)
class LabelTarget:
    """A geometry-bearing object eligible for an overview label."""

    target_id: str
    target_type: str
    source_item_id: str
    geometry: Mapping[str, Any]
    anchor_point: Point
    bbox: Box
    priority: int = 50
    label_role: str = "capture"
    status: str = "ready"
    warning_ids: tuple[str, ...] = ()
    style_hint: str = ""
    metadata: Mapping[str, Any] | None = None


@dataclass(frozen=True)
class LabelContent:
    """Text and visual metadata requested for one target label."""

    label_id: str
    target_id: str
    title: str
    subtitle: str = ""
    detail_lines: tuple[str, ...] = ()
    badges: tuple[str, ...] = ()
    severity: str = ""
    metadata_fields: tuple[tuple[str, str], ...] = ()
    max_width_px: int = 168
    min_width_px: int = 72
    priority: int = 50


@dataclass(frozen=True)
class LabelPlacementPolicy:
    """Rules used by the layout planner to place label boxes."""

    strategy: str = "outside_edge_callouts"
    allowed_zones: tuple[str, ...] = (
        "left_margin",
        "right_margin",
        "top_margin",
        "bottom_margin",
    )
    margin_px: int = 120
    label_spacing_px: int = 8
    avoid_target_overlap: bool = True
    avoid_label_overlap: bool = True
    avoid_layout_overlap: bool = True
    avoid_leader_crossing: bool = True
    max_iterations: int = 4
    fallback_strategy: str = "omit_low_priority"


@dataclass(frozen=True)
class OverviewStylePolicy:
    """Visual styling knobs for overview diagrams."""

    target_box_style: str = "#38bdf8"
    selected_target_style: str = "#22d3ee"
    warning_target_style: str = "#fbbf24"
    label_box_style: str = "#111827"
    leader_style: str = "#67e8f9"
    badge_style: str = "#f59e0b"
    background_style: str = "#0b1120"
    text_style: str = "#f8fafc"
    secondary_text_style: str = "#cbd5e1"
    font_policy: Mapping[str, Any] | None = None
    color_policy: Mapping[str, str] | None = None
    opacity_policy: Mapping[str, float] | None = None


@dataclass(frozen=True)
class LabelBox:
    """Concrete placed label bounds and content."""

    label_id: str
    target_id: str
    text_lines: tuple[str, ...]
    bounds: Box
    style: str
    priority: int
    detail_level: str = "standard"
    status: str = "placed"


@dataclass(frozen=True)
class LeaderPath:
    """Polyline connecting one label to one target."""

    leader_id: str
    target_id: str
    label_id: str
    points: tuple[Point, ...]
    style: str = "#475569"
    crossing_count: int = 0
    collision_warnings: tuple[str, ...] = ()


@dataclass(frozen=True)
class PlacementMetadata:
    """Summary of label placement quality and fallback behavior."""

    strategy_used: str
    labels_requested: int
    labels_placed: int
    labels_omitted: int = 0
    collisions_resolved: int = 0
    unresolved_collisions: int = 0
    fallback_steps_used: tuple[str, ...] = ()


@dataclass(frozen=True)
class OverviewDiagramScene:
    """Renderer-neutral scene for editor preview, reports, and exports."""

    scene_id: str
    title: str
    source_image_artifact_id: str
    canvas_size: tuple[int, int]
    layout_bounds: Box
    target_shapes: tuple[LabelTarget, ...]
    label_boxes: tuple[LabelBox, ...]
    leader_paths: tuple[LeaderPath, ...]
    legend: tuple[str, ...] = ()
    badges: tuple[str, ...] = ()
    scale_bar: Optional[Mapping[str, Any]] = None
    warnings: tuple[str, ...] = ()
    placement_metadata: PlacementMetadata = PlacementMetadata("outside_edge_callouts", 0, 0)
