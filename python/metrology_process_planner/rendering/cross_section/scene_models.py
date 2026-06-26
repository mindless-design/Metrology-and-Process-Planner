"""Serializable cross-section scene model independent of drawing backends."""

from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Any


@dataclass(frozen=True)
class LabelCandidate:
    """Potential label target generated before collision-aware placement."""

    target_id: str
    text: str
    priority: int
    preferred_positions: tuple[str, ...]
    allowed_positions: tuple[str, ...]
    anchor_point: tuple[float, float]
    leader_allowed: bool = True
    inline_allowed: bool = True
    min_font_size: int = 9
    max_font_size: int = 13
    collision_group: str = "material"


@dataclass(frozen=True)
class PlacedLabel:
    """A concrete label placement with collision status."""

    label_id: str
    target_id: str
    text: str
    position: tuple[float, float]
    anchor_point: tuple[float, float]
    placement_type: str
    bounding_box: tuple[float, float, float, float]
    leader_line: tuple[tuple[float, float], tuple[float, float]] | None = None
    priority: int = 0
    collision_status: str = "resolved"


@dataclass(frozen=True)
class LegendEntry:
    """One visible legend row."""

    material_id: str
    label: str
    color: str
    notes: tuple[str, ...] = ()


@dataclass(frozen=True)
class LegendModel:
    """Legend entries and display behavior."""

    entries: tuple[LegendEntry, ...]
    compact: bool = False
    group_by_material_category: bool = False
    show_only_visible_materials: bool = True
    show_exaggeration_notes: bool = False
    show_compression_notes: bool = False


@dataclass(frozen=True)
class CompressionMetadata:
    """Durable metadata for non-physical z transforms."""

    enabled: bool
    transform_type: str
    physical_z_ranges: tuple[tuple[float, float], ...] = ()
    visual_z_ranges: tuple[tuple[float, float], ...] = ()
    affected_materials: tuple[str, ...] = ()
    compression_ratios: tuple[float, ...] = ()
    break_marks: tuple[tuple[float, float], ...] = ()
    min_thickness_overrides: tuple[tuple[str, float, float], ...] = ()
    notes: tuple[str, ...] = ()


@dataclass(frozen=True)
class MaterialShape:
    """One drawable material region with physical and visual geometry."""

    shape_id: str
    material_id: str
    material_name: str
    process_step_id: str
    physical_geometry: tuple[float, float, float, float]
    visual_geometry: tuple[float, float, float, float]
    physical_bounds: tuple[float, float, float, float]
    visual_bounds: tuple[float, float, float, float]
    visible: bool
    visual_style: dict[str, str]
    label_candidates: tuple[LabelCandidate, ...] = ()
    thin_layer_flag: bool = False
    compressed_flag: bool = False
    exaggerated_flag: bool = False


@dataclass(frozen=True)
class CrossSectionSceneModel:
    """A backend-independent cross-section scene."""

    scene_id: str
    render_mode_id: str
    title: str
    physical_units: str
    visual_units: str
    coordinate_frame: dict[str, object]
    material_shapes: tuple[MaterialShape, ...]
    surface_profiles: tuple[tuple[tuple[float, float], ...], ...] = ()
    axes: tuple[dict[str, object], ...] = ()
    scale_bars: tuple[dict[str, object], ...] = ()
    labels: tuple[PlacedLabel, ...] = ()
    leaders: tuple[dict[str, object], ...] = ()
    callouts: tuple[dict[str, object], ...] = ()
    legend: LegendModel | None = None
    annotations: tuple[dict[str, object], ...] = ()
    highlights: tuple[dict[str, object], ...] = ()
    compression_metadata: CompressionMetadata = CompressionMetadata(False, "physical_linear")
    warnings: tuple[str, ...] = ()
    source_refs: dict[str, str] | None = None


def scene_to_dict(scene: CrossSectionSceneModel) -> dict[str, Any]:
    """Serialize a cross-section scene to JSON-compatible data."""

    return asdict(scene)


def scene_from_dict(data: dict[str, Any]) -> CrossSectionSceneModel:
    """Build a cross-section scene from JSON-compatible data."""

    shapes = tuple(_shape(item) for item in data.get("material_shapes", ()))
    labels = tuple(_placed_label(item) for item in data.get("labels", ()))
    legend_data = data.get("legend")
    compression = CompressionMetadata(**data.get("compression_metadata", {}))
    return CrossSectionSceneModel(
        **_scene_identity(data),
        material_shapes=shapes,
        surface_profiles=_surface_profiles(data),
        axes=_dict_tuple(data, "axes"),
        scale_bars=_dict_tuple(data, "scale_bars"),
        labels=labels,
        leaders=_dict_tuple(data, "leaders"),
        callouts=_dict_tuple(data, "callouts"),
        legend=_legend(legend_data) if isinstance(legend_data, dict) else None,
        annotations=_dict_tuple(data, "annotations"),
        highlights=_dict_tuple(data, "highlights"),
        compression_metadata=compression,
        warnings=tuple(str(item) for item in data.get("warnings", ())),
        source_refs=dict(data.get("source_refs", {})),
    )


def _scene_identity(data: dict[str, Any]) -> dict[str, Any]:
    return {
        "scene_id": str(data.get("scene_id", "")),
        "render_mode_id": str(data.get("render_mode_id", "")),
        "title": str(data.get("title", "")),
        "physical_units": str(data.get("physical_units", "nm")),
        "visual_units": str(data.get("visual_units", "px")),
        "coordinate_frame": dict(data.get("coordinate_frame", {})),
    }


def _surface_profiles(data: dict[str, Any]) -> tuple[tuple[tuple[Any, ...], ...], ...]:
    return tuple(
        tuple(tuple(point) for point in item)
        for item in data.get("surface_profiles", ())
    )


def _dict_tuple(data: dict[str, Any], key: str) -> tuple[dict[str, Any], ...]:
    return tuple(dict(item) for item in data.get(key, ()))

def _shape(data: dict[str, Any]) -> MaterialShape:
    candidates = tuple(LabelCandidate(**item) for item in data.get("label_candidates", ()))
    return MaterialShape(
        shape_id=str(data.get("shape_id", "")),
        material_id=str(data.get("material_id", "")),
        material_name=str(data.get("material_name", "")),
        process_step_id=str(data.get("process_step_id", "")),
        physical_geometry=tuple(data.get("physical_geometry", (0, 0, 0, 0))),
        visual_geometry=tuple(data.get("visual_geometry", (0, 0, 0, 0))),
        physical_bounds=tuple(data.get("physical_bounds", (0, 0, 0, 0))),
        visual_bounds=tuple(data.get("visual_bounds", (0, 0, 0, 0))),
        visible=bool(data.get("visible", True)),
        visual_style=dict(data.get("visual_style", {})),
        label_candidates=candidates,
        thin_layer_flag=bool(data.get("thin_layer_flag", False)),
        compressed_flag=bool(data.get("compressed_flag", False)),
        exaggerated_flag=bool(data.get("exaggerated_flag", False)),
    )


def _placed_label(data: dict[str, Any]) -> PlacedLabel:
    leader = data.get("leader_line")
    return PlacedLabel(
        label_id=str(data.get("label_id", "")),
        target_id=str(data.get("target_id", "")),
        text=str(data.get("text", "")),
        position=tuple(data.get("position", (0, 0))),
        anchor_point=tuple(data.get("anchor_point", (0, 0))),
        placement_type=str(data.get("placement_type", "legend_only")),
        bounding_box=tuple(data.get("bounding_box", (0, 0, 0, 0))),
        leader_line=(tuple(leader[0]), tuple(leader[1])) if leader else None,
        priority=int(data.get("priority", 0)),
        collision_status=str(data.get("collision_status", "resolved")),
    )


def _legend(data: dict[str, Any]) -> LegendModel:
    return LegendModel(
        entries=tuple(LegendEntry(**item) for item in data.get("entries", ())),
        compact=bool(data.get("compact", False)),
        group_by_material_category=bool(data.get("group_by_material_category", False)),
        show_only_visible_materials=bool(data.get("show_only_visible_materials", True)),
        show_exaggeration_notes=bool(data.get("show_exaggeration_notes", False)),
        show_compression_notes=bool(data.get("show_compression_notes", False)),
    )
