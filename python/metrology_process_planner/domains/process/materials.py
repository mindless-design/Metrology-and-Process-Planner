"""Material and layout-layer references for process recipes."""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
from typing import Any

PALETTE_VARIANTS = ("normal", "high_contrast", "print_safe")


@dataclass(frozen=True)
class Material:
    """A process material with display properties."""

    id: str
    name: str
    color: str
    visible: bool = True
    category: str = ""
    hatch_style: str = ""
    physical_role: str = ""
    notes: str = ""
    aliases: tuple[str, ...] = ()
    role: str = ""

    def to_dict(self) -> dict[str, Any]:
        """Serialize the material to JSON-compatible data."""

        return {
            "id": self.id,
            "name": self.name,
            "color": self.color,
            "visible": self.visible,
            "category": self.category,
            "hatch_style": self.hatch_style,
            "physical_role": self.physical_role,
            "notes": self.notes,
            "aliases": list(self.aliases),
            "role": self.role or self.physical_role,
        }

    @classmethod
    def from_dict(cls, data: Mapping[str, Any]) -> Material:
        """Build a material from saved JSON-compatible data."""

        return cls(
            id=str(data["id"]),
            name=str(data.get("name", data["id"])),
            color=str(data.get("color", "#888888")),
            visible=bool(data.get("visible", True)),
            category=str(data.get("category", "")),
            hatch_style=str(data.get("hatch_style", data.get("style", ""))),
            physical_role=str(data.get("physical_role", "")),
            notes=str(data.get("notes", "")),
            aliases=tuple(str(item) for item in data.get("aliases", ())),
            role=str(data.get("role", data.get("physical_role", ""))),
        )


@dataclass(frozen=True)
class LayerReference:
    """A process step reference to a KLayout layer/datatype pair."""

    source: str
    layer: int
    datatype: int = 0
    name: str = ""

    def to_dict(self) -> dict[str, Any]:
        """Serialize the layer reference to JSON-compatible data."""

        return {
            "source": self.source,
            "layer": self.layer,
            "datatype": self.datatype,
            "name": self.name,
        }

    @classmethod
    def from_dict(cls, data: Mapping[str, Any]) -> LayerReference:
        """Build a layer reference from saved JSON-compatible data."""

        return cls(
            source=str(data.get("source", "layout")),
            layer=int(data["layer"]),
            datatype=int(data.get("datatype", 0)),
            name=str(data.get("name", "")),
        )


def material_catalog() -> tuple[Material, ...]:
    """Return the built-in semiconductor material catalog."""

    return (
        _material("Si", "Silicon", "#8a8f98", "semiconductor", ("silicon",), "structural"),
        _material("SiO2", "Oxide", "#69aee8", "dielectric",
                  ("oxide", "silicon dioxide", "sio2"), "structural"),
        _material("Si3N4", "Silicon nitride", "#a78bfa", "dielectric",
                  ("nitride", "silicon nitride", "sin", "si3n4"), "structural"),
        _material("Al2O3", "ALD Al2O3", "#f2c94c", "dielectric",
                  ("al2o3", "ald al2o3", "alumina", "aluminum oxide"), "structural"),
        _material("native_oxide", "Native oxide", "#c4e6ff", "dielectric",
                  ("native oxide",), "structural"),
        _material("photoresist", "Photoresist", "#d946ef", "polymer",
                  ("resist", "pr", "photo resist"), "mask"),
        _material("poly-Si", "Polysilicon", "#7dd3fc", "semiconductor",
                  ("poly", "poly-si", "polysilicon"), "structural"),
        _material("Al", "Aluminum", "#d1d5db", "metal", ("aluminum", "al"), "structural"),
        _material("Cu", "Copper", "#c87533", "metal", ("copper", "cu"), "structural"),
        _material("W", "Tungsten", "#9ca3af", "metal", ("tungsten", "w"), "structural"),
        _material("TiN", "Titanium nitride", "#b59f3b", "metal",
                  ("tin", "titanium nitride"), "structural"),
        _material("air/void", "Air / void", "#ffffff", "void",
                  ("air", "void", "gap"), "void"),
        _material("generic metal", "Generic metal", "#b8bcc4", "metal",
                  ("metal", "generic_metal"), "structural"),
        _material("generic dielectric", "Generic dielectric", "#98d8c8", "dielectric",
                  ("dielectric", "insulator", "generic_dielectric"), "structural"),
        _material("unknown", "Unknown material", "#ff4d4d", "unknown",
                  ("unknown", "unresolved"), "unknown"),
    )


def resolve_material(value: str, catalog: tuple[Material, ...] | None = None) -> Material:
    """Resolve a material id, display name, or alias to a catalog material."""

    lookup = _material_lookup(catalog or material_catalog())
    return lookup.get(_key(value), lookup["unknown"])


def material_style(
    value: str,
    *,
    palette: str = "normal",
    catalog: tuple[Material, ...] | None = None,
) -> dict[str, str]:
    """Return deterministic renderer style metadata for a material."""

    material = resolve_material(value, catalog)
    color = _palette_color(material, palette)
    stroke = "#111827" if palette != "high_contrast" else "#000000"
    if (material.role or material.physical_role) in {"mask", "temporary"}:
        stroke = "#f9a8d4"
    if material.id == "unknown":
        stroke = "#7f1d1d"
    return {
        "fill": color,
        "stroke": stroke,
        "material_id": material.id,
        "material_name": material.name,
        "category": material.category,
        "role": material.role or material.physical_role,
    }


def material_catalog_with(
    material_ids: tuple[str, ...],
    catalog: tuple[Material, ...] | None = None,
) -> tuple[Material, ...]:
    """Return catalog materials needed by a recipe, including unknown fallback."""

    resolved: dict[str, Material] = {}
    for material_id in material_ids:
        material = resolve_material(material_id, catalog)
        resolved[material.id] = material
    return tuple(resolved.values())


def _material(
    material_id: str,
    name: str,
    color: str,
    category: str,
    aliases: tuple[str, ...],
    role: str,
) -> Material:
    return Material(
        material_id,
        name,
        color,
        category=category,
        physical_role=role,
        aliases=aliases,
        role=role,
    )


def _material_lookup(catalog: tuple[Material, ...]) -> dict[str, Material]:
    lookup: dict[str, Material] = {}
    for material in catalog:
        lookup[_key(material.id)] = material
        lookup[_key(material.name)] = material
        for alias in material.aliases:
            lookup[_key(alias)] = material
    return lookup


def _key(value: str) -> str:
    return str(value or "").strip().lower().replace("_", " ")


def _palette_color(material: Material, palette: str) -> str:
    if palette == "high_contrast":
        return {
            "SiO2": "#00a6ff",
            "Si3N4": "#8b5cf6",
            "photoresist": "#ff2bd6",
            "unknown": "#ff0000",
        }.get(material.id, material.color)
    if palette == "print_safe":
        return {
            "photoresist": "#cc79a7",
            "Cu": "#d55e00",
            "SiO2": "#56b4e9",
            "Si3N4": "#0072b2",
            "unknown": "#cc0000",
        }.get(material.id, material.color)
    return material.color
