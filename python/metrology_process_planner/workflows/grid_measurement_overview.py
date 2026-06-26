"""Grid overview artifact rendering helpers."""

from __future__ import annotations

from dataclasses import replace
from html import escape
from pathlib import Path
from typing import Any

from metrology_process_planner.domains.artifacts.artifact_ids import artifact_id
from metrology_process_planner.domains.session import (
    ArtifactFileMetadata,
    ArtifactOwnerRef,
    ArtifactRecord,
    ArtifactRepairMetadata,
    ArtifactStatus,
    GridDatasetRecord,
    WarningRecord,
)


def grid_overview_placeholder(dataset: GridDatasetRecord, warning_id: str) -> ArtifactRecord:
    """Return a placeholder overview artifact for a grid dataset."""

    return ArtifactRecord(
        artifact_id("grid_dataset", dataset.id, "grid_overview"),
        "grid_overview",
        "Grid Overview",
        f"artifacts/grid/{dataset.id}-overview.svg",
        ArtifactOwnerRef("grid_dataset", dataset.id, "grid_overview"),
        status=ArtifactStatus.PLACEHOLDER,
        generator="grid_measurement_workflow",
        repair=ArtifactRepairMetadata("generate_grid_overview", "Generate grid overview."),
        warning_ids=(warning_id,),
    )


def present_grid_overview(
    dataset: GridDatasetRecord,
    svg_text: str,
    output_folder: Path,
) -> ArtifactRecord:
    """Write and return a present grid overview artifact record."""

    relative_path = f"artifacts/grid/{dataset.id}-overview.svg"
    destination = output_folder / relative_path
    destination.parent.mkdir(parents=True, exist_ok=True)
    destination.write_text(svg_text, encoding="utf-8")
    return ArtifactRecord(
        artifact_id("grid_dataset", dataset.id, "grid_overview"),
        "grid_overview",
        "Grid Overview",
        relative_path,
        ArtifactOwnerRef("grid_dataset", dataset.id, "grid_overview"),
        status=ArtifactStatus.PRESENT,
        generator="grid_measurement_workflow",
        repair=ArtifactRepairMetadata(
            "generate_grid_overview",
            "Regenerate grid overview.",
            regenerable=True,
        ),
        file=ArtifactFileMetadata(
            size_bytes=len(svg_text.encode("utf-8")),
            width_px=640,
            height_px=480,
            content_type="image/svg+xml",
        ),
        warning_ids=(),
        extensions={"planned_site_count": len(_planned_sites(dataset))},
    )


def grid_overview_placeholder_warning(dataset: GridDatasetRecord) -> WarningRecord:
    """Return the warning associated with a placeholder grid overview."""

    return WarningRecord(
        f"warning-grid-overview-{dataset.id}-placeholder",
        "Grid overview artifact is a placeholder until generated.",
        source="grid_measurement",
        code="GRID_OVERVIEW_PLACEHOLDER",
        related_item_refs=(f"grid:{dataset.id}",),
        related_artifact_refs=(artifact_id("grid_dataset", dataset.id, "grid_overview"),),
        repair_suggestion="Generate the grid overview artifact.",
    )


def grid_overview_svg(dataset: GridDatasetRecord) -> str:
    """Return an SVG grid overview from planned site metadata."""

    sites = _planned_sites(dataset)
    points = tuple(_site_point(site) for site in sites)
    bounds = _point_bounds(points)
    title = escape(dataset.label or dataset.id)
    circles = "\n".join(_site_circle(site, bounds) for site in sites)
    return (
        '<svg xmlns="http://www.w3.org/2000/svg" width="640" height="480" '
        'viewBox="0 0 640 480">\n'
        '<rect x="0" y="0" width="640" height="480" fill="#f8fafc"/>\n'
        '<rect x="40" y="52" width="560" height="368" fill="#ffffff" '
        'stroke="#334155" stroke-width="1.5"/>\n'
        f'<text x="40" y="30" font-family="Arial, sans-serif" font-size="18" '
        f'fill="#0f172a">{title}</text>\n'
        f"{circles}\n"
        "</svg>\n"
    )


def clear_grid_placeholder_warning(
    dataset: GridDatasetRecord,
    warning_id: str,
) -> GridDatasetRecord:
    """Return a dataset with one placeholder warning removed."""

    warning_ids = tuple(item for item in dataset.warning_ids if item != warning_id)
    return replace(dataset, warning_ids=warning_ids)


def _site_circle(site: dict[str, Any], bounds: tuple[float, float, float, float]) -> str:
    x, y = _site_point(site)
    px = _scale(x, bounds[0], bounds[2], 60.0, 580.0)
    py = _scale(y, bounds[1], bounds[3], 400.0, 72.0)
    label = escape(str(site.get("sequence") or site.get("id") or ""))
    return (
        f'<circle cx="{px:.2f}" cy="{py:.2f}" r="6" fill="#2563eb" />'
        f'<text x="{px + 9:.2f}" y="{py + 4:.2f}" '
        f'font-family="Arial, sans-serif" font-size="10" fill="#334155">{label}</text>'
    )


def _scale(
    value: float,
    source_min: float,
    source_max: float,
    target_min: float,
    target_max: float,
) -> float:
    if source_max == source_min:
        return (target_min + target_max) / 2.0
    return target_min + ((value - source_min) / (source_max - source_min)) * (
        target_max - target_min
    )


def _point_bounds(points: tuple[tuple[float, float], ...]) -> tuple[float, float, float, float]:
    if not points:
        return (0.0, 0.0, 1.0, 1.0)
    xs = tuple(point[0] for point in points)
    ys = tuple(point[1] for point in points)
    return (min(xs), min(ys), max(xs), max(ys))


def _site_point(site: dict[str, Any]) -> tuple[float, float]:
    center = dict(site.get("center", {}))
    return (float(center.get("x", 0.0)), float(center.get("y", 0.0)))


def _planned_sites(dataset: GridDatasetRecord) -> tuple[dict[str, Any], ...]:
    sites = dict(dataset.extensions or {}).get("planned_sites", ())
    if isinstance(sites, list):
        sites = tuple(sites)
    if not isinstance(sites, tuple):
        return ()
    return tuple(dict(site) for site in sites if isinstance(site, dict))
