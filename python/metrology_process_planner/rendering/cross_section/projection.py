"""Render-space projection and visual transform planning."""

from __future__ import annotations

from dataclasses import dataclass

from metrology_process_planner.domains.process import (
    Material,
    MaterialInterval,
    StackGeometry2D,
    resolve_material,
)
from metrology_process_planner.rendering.cross_section.models import RenderIntent, VisualTransform
from metrology_process_planner.rendering.cross_section.projection_helpers import (
    column_edges,
    geometry_bounds,
    material_shape,
    override_notes,
)
from metrology_process_planner.rendering.cross_section.scene_models import (
    CompressionMetadata,
    MaterialShape,
)


@dataclass(frozen=True)
class RenderProjectionPlan:
    """Filtered physical geometry mapped into visual-space shapes."""

    shapes: tuple[MaterialShape, ...]
    visual_transform: VisualTransform
    compression_metadata: CompressionMetadata
    warnings: tuple[str, ...] = ()


def build_render_projection(
    geometry: StackGeometry2D,
    intent: RenderIntent,
    materials: tuple[Material, ...] = (),
) -> RenderProjectionPlan:
    """Build material shapes for physical, compressed, or illustrative modes."""

    material_lookup = _material_lookup(materials)
    bounds = geometry_bounds(geometry)
    mapper = _ZMapper(bounds[1], bounds[3], intent)
    shapes: list[MaterialShape] = []
    warnings: list[str] = []
    overrides: list[tuple[str, float, float]] = []
    for column_index, (left, right, column) in enumerate(column_edges(geometry)):
        for interval_index, interval in enumerate(column.intervals):
            shape, override = _project_interval(
                column_index,
                interval_index,
                (left, right),
                interval,
                mapper,
                intent,
                material_lookup,
            )
            shapes.append(shape)
            if override:
                overrides.append(override)
                warnings.append("RENDER_THIN_LAYER_EXAGGERATED")
    metadata = mapper.metadata(tuple(overrides))
    if metadata.enabled:
        warnings.append("RENDER_COMPRESSION_APPLIED")
    return _projection_plan(shapes, mapper, overrides, metadata, warnings)


def _projection_plan(
    shapes: list[MaterialShape],
    mapper: _ZMapper,
    overrides: list[tuple[str, float, float]],
    metadata: CompressionMetadata,
    warnings: list[str],
) -> RenderProjectionPlan:
    return RenderProjectionPlan(
        tuple(shapes),
        mapper.transform(tuple(overrides)),
        metadata,
        tuple(dict.fromkeys(warnings)),
    )


def _project_interval(
    column_index: int,
    interval_index: int,
    x_bounds: tuple[float, float],
    interval: MaterialInterval,
    mapper: _ZMapper,
    intent: RenderIntent,
    material_lookup: dict[str, Material],
) -> tuple[MaterialShape, tuple[str, float, float] | None]:
    material_id = interval.material_id
    visual_min = mapper.map_z(interval.z_min)
    visual_max = mapper.map_z(interval.z_max)
    physical_thickness = abs(interval.z_max - interval.z_min)
    visual_min, visual_max, exaggerated = _enforce_min_thickness(
        visual_min,
        visual_max,
        physical_thickness,
        intent,
    )
    material = material_lookup.get(_material_key(material_id)) or resolve_material(material_id)
    compressed = mapper.compressed and interval.z_min < mapper.threshold
    shape = material_shape(
        column_index,
        interval_index,
        material_id,
        material.name if material else material_id,
        material.color if material else "#888888",
        (x_bounds[0], interval.z_min, x_bounds[1], interval.z_max),
        (x_bounds[0], visual_min, x_bounds[1], visual_max),
        physical_thickness,
        compressed,
        exaggerated,
    )
    override = None
    if exaggerated:
        override = (material_id, physical_thickness, abs(visual_max - visual_min))
    return shape, override


def _material_lookup(materials: tuple[Material, ...]) -> dict[str, Material]:
    lookup: dict[str, Material] = {}
    for material in materials:
        lookup[_material_key(material.id)] = material
        lookup[_material_key(material.name)] = material
        for alias in material.aliases:
            lookup[_material_key(alias)] = material
    return lookup


def _material_key(value: str) -> str:
    return str(value or "").strip().lower().replace("_", " ")


class _ZMapper:
    def __init__(self, bottom: float, top: float, intent: RenderIntent) -> None:
        self.bottom = bottom
        self.top = top
        self.intent = intent
        policy = intent.compression_policy
        self.compressed = bool(policy.enabled and top > bottom)
        preserve = policy.preserve_top_n_nm or max((top - bottom) * 0.2, 1.0)
        self.threshold = max(bottom, top - preserve)
        self.ratio = max(1.0, min(policy.max_compression_ratio, top - bottom))

    def map_z(self, z: float) -> float:
        """Map physical z to visual z."""

        if not self.compressed or z >= self.threshold:
            return z
        return self.threshold - ((self.threshold - z) / self.ratio)

    def metadata(self, overrides: tuple[tuple[str, float, float], ...]) -> CompressionMetadata:
        """Return durable compression metadata."""

        if not self.compressed:
            return CompressionMetadata(
                False,
                "physical_linear",
                min_thickness_overrides=overrides,
                notes=override_notes(overrides),
            )
        physical = ((self.bottom, self.threshold),)
        visual = ((self.map_z(self.bottom), self.map_z(self.threshold)),)
        return CompressionMetadata(
            True,
            "piecewise_linear_compressed",
            physical_z_ranges=physical,
            visual_z_ranges=visual,
            compression_ratios=(self.ratio,),
            break_marks=((0.0, self.map_z(self.threshold)),),
            min_thickness_overrides=overrides,
            notes=("Thick regions were compressed in render space.",) + override_notes(overrides),
        )

    def transform(self, overrides: tuple[tuple[str, float, float], ...]) -> VisualTransform:
        """Return physical-to-visual transform metadata."""

        transform = "piecewise_linear_compressed" if self.compressed else "physical_linear"
        return VisualTransform(
            z_transform=transform,
            min_visual_thickness=self.intent.exaggeration_policy.min_visual_thickness_px,
            compression_regions=((self.bottom, self.threshold),) if self.compressed else (),
            break_marks=((0.0, self.map_z(self.threshold)),) if self.compressed else (),
            exaggeration_annotations=tuple(item[0] for item in overrides),
            mapping_physical_to_visual=((self.bottom, self.map_z(self.bottom)),
                                        (self.top, self.map_z(self.top))),
        )


def _enforce_min_thickness(
    visual_min: float,
    visual_max: float,
    physical_thickness: float,
    intent: RenderIntent,
) -> tuple[float, float, bool]:
    policy = intent.exaggeration_policy
    current = abs(visual_max - visual_min)
    if not policy.enabled or current >= policy.min_visual_thickness_px or physical_thickness <= 0:
        return visual_min, visual_max, False
    ratio = policy.min_visual_thickness_px / max(current, 0.000001)
    if ratio > policy.max_exaggeration_ratio and policy.prefer_callout_when_too_thin:
        return visual_min, visual_max, False
    center = (visual_min + visual_max) / 2.0
    half = policy.min_visual_thickness_px / 2.0
    return center - half, center + half, True
