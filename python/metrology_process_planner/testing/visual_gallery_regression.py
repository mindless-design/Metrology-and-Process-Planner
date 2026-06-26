"""Golden comparison helpers for generated visual review gallery items."""

from __future__ import annotations

import json
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any

from metrology_process_planner.testing.visual_regression import compare_json


@dataclass(frozen=True)
class VisualGalleryComparison:
    """Machine-readable comparison result for one gallery item."""

    status: str
    golden_path: str = ""
    actual_path: str = ""
    debug_path: str = ""
    differences: tuple[str, ...] = ()

    def to_dict(self) -> dict[str, Any]:
        """Return JSON-compatible comparison data."""

        data = asdict(self)
        data["differences"] = list(self.differences)
        return data


def compare_gallery_item(
    root: Path,
    item: Any,
    golden_root: Path,
    debug_root: Path,
) -> VisualGalleryComparison:
    """Compare a gallery item with a configured golden when one exists."""

    if not item.metadata_path:
        return VisualGalleryComparison("not_configured")
    golden_path = golden_root / _golden_name(item.source_fixture, item.render_profile)
    if not golden_path.exists():
        return VisualGalleryComparison("not_configured")
    scene_path = root / item.metadata_path
    actual = _scene_summary(scene_path, item.source_fixture, item.render_profile)
    expected = json.loads(golden_path.read_text(encoding="utf-8"))
    comparison = compare_json(expected, actual)
    if comparison.matched:
        return VisualGalleryComparison(
            "matched",
            _rel(golden_path),
            item.metadata_path,
        )
    debug_path = _write_debug(debug_root, item.artifact_id, expected, actual)
    return VisualGalleryComparison(
        "mismatch",
        _rel(golden_path),
        item.metadata_path,
        _rel(debug_path),
        comparison.differences,
    )


def comparison_status(comparison: VisualGalleryComparison) -> str:
    """Return the manifest comparison status string."""

    return comparison.status


def _scene_summary(scene_path: Path, recipe_id: str, profile_id: str) -> dict[str, Any]:
    data = json.loads(scene_path.read_text(encoding="utf-8"))
    material_counts: dict[str, int] = {}
    for shape in data.get("material_shapes", ()):
        material_id = str(shape.get("material_id", ""))
        material_counts[material_id] = material_counts.get(material_id, 0) + 1
    compression = dict(data.get("compression_metadata", {}))
    return {
        "recipe_id": recipe_id,
        "profile_id": profile_id,
        "render_mode_id": str(data.get("render_mode_id", "")),
        "shape_count": len(data.get("material_shapes", ())),
        "materials": dict(sorted(material_counts.items())),
        "label_count": len(data.get("labels", ())),
        "warnings": sorted(str(item) for item in data.get("warnings", ())),
        "compression_enabled": bool(compression.get("enabled", False)),
        "compressed_materials": sorted(
            str(item) for item in compression.get("affected_materials", ())
        ),
        "thin_layer_shape_count": sum(
            1 for shape in data.get("material_shapes", ())
            if bool(shape.get("exaggerated_flag", False))
        ),
    }


def _golden_name(source_fixture: str, render_profile: str) -> str:
    return f"{source_fixture}.{render_profile}.expected.json"


def _write_debug(
    debug_root: Path,
    artifact_id: str,
    expected: object,
    actual: object,
) -> Path:
    path = debug_root / f"{_safe_name(artifact_id)}.visual-gallery-comparison.json"
    path.parent.mkdir(parents=True, exist_ok=True)
    payload = {"expected": expected, "actual": actual}
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return path


def _safe_name(value: str) -> str:
    return "".join(char if char.isalnum() or char in {"-", "_"} else "_" for char in value)


def _rel(path: Path) -> str:
    try:
        return str(path.relative_to(Path.cwd())).replace("\\", "/")
    except ValueError:
        return str(path).replace("\\", "/")
