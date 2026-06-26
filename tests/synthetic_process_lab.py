"""Synthetic process regression helpers shared by fixture tests."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, cast

from tests.synthetic_process_models import (
    GDS_ROOT,
    GOLDEN_ROOT,
    OUTPUT_ROOT,
    RECIPE_ROOT,
    SESSION_ROOT,
    CutlineSample,
    ExtractedRect,
    GeometryExtractionWarning,
    GeometrySnapshot,
    MaskInterval,
    PointSample,
)

__all__ = [
    "GDS_ROOT",
    "GOLDEN_ROOT",
    "OUTPUT_ROOT",
    "RECIPE_ROOT",
    "SESSION_ROOT",
    "CutlineSample",
    "ExtractedRect",
    "GeometryExtractionWarning",
    "GeometrySnapshot",
    "MaskInterval",
    "PointSample",
    "cutline_sample",
    "extract_structure",
    "layer_coverage",
    "load_manifest",
    "load_rectangles",
    "point_sample",
    "require_layer",
    "write_debug_json",
]


def load_manifest() -> dict[str, Any]:
    """Load the synthetic GDS sidecar manifest."""

    return cast(
        dict[str, Any],
        json.loads((GDS_ROOT / "process_planner_testchip.geometry.json").read_text()),
    )


def load_rectangles() -> tuple[ExtractedRect, ...]:
    """Load deterministic rectangles from the geometry manifest."""

    return tuple(ExtractedRect(**item) for item in load_manifest()["rectangles"])


def extract_structure(
    structure: str,
    roi: tuple[float, float, float, float] | None = None,
) -> GeometrySnapshot:
    """Extract rectangles for one named synthetic structure."""

    rects = [rect for rect in load_rectangles() if rect.structure == structure]
    if roi is not None:
        rects = [rect for rect in rects if rect.intersects_roi(roi)]
    warnings: tuple[GeometryExtractionWarning, ...] = ()
    if not rects:
        warnings = (GeometryExtractionWarning("GEOMETRY_STRUCTURE_EMPTY", structure),)
    return GeometrySnapshot(structure, tuple(sorted(rects, key=_rect_key)), warnings)


def require_layer(
    snapshot: GeometrySnapshot,
    layer_name: str,
) -> tuple[GeometryExtractionWarning, ...]:
    """Return a warning if the snapshot lacks the requested layer."""

    if layer_name in snapshot.layer_names():
        return ()
    return (
        GeometryExtractionWarning(
            "GEOMETRY_LAYER_MISSING",
            f"Missing layer {layer_name}.",
            layer_name,
        ),
    )


def point_sample(structure: str, x: float, y: float) -> PointSample:
    """Return layer and rectangle membership for one point."""

    rects = [rect for rect in extract_structure(structure).rectangles if rect.contains_point(x, y)]
    return PointSample(
        x,
        y,
        tuple(sorted({rect.layer_name for rect in rects})),
        tuple(rect.name for rect in sorted(rects, key=_rect_key)),
    )


def cutline_sample(
    structure: str,
    y: float,
    layer_name: str | None = None,
) -> CutlineSample:
    """Extract deterministic mask intervals along a horizontal cutline."""

    rects = [rect for rect in extract_structure(structure).rectangles if rect.crosses_y(y)]
    if layer_name is not None:
        rects = [rect for rect in rects if rect.layer_name == layer_name]
    intervals = tuple(
        MaskInterval(rect.layer_name, rect.x_min, rect.x_max, rect.name)
        for rect in sorted(rects, key=_rect_key)
    )
    return CutlineSample(structure, y, intervals)


def layer_coverage(snapshot: GeometrySnapshot) -> dict[str, float]:
    """Return total rectangular area by layer."""

    coverage: dict[str, float] = {}
    for rect in snapshot.rectangles:
        coverage[rect.layer_name] = round(coverage.get(rect.layer_name, 0.0) + (
            (rect.x_max - rect.x_min) * (rect.y_max - rect.y_min)
        ), 6)
    return dict(sorted(coverage.items()))


def write_debug_json(name: str, payload: object) -> Path:
    """Write failure/debug payloads for regression tests."""

    target = OUTPUT_ROOT / "debug" / name
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n")
    return target


def _rect_key(rect: ExtractedRect) -> tuple[str, str, float, float, float, float]:
    return (rect.layer_name, rect.name, rect.x_min, rect.y_min, rect.x_max, rect.y_max)
