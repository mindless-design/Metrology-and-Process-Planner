"""Geometry-focused visual QA checks for selected capture features."""

from __future__ import annotations

from pathlib import Path

from metrology_process_planner.testing.visual_quality_models import VisualIssue


def selected_line_issue(
    width_px: int,
    height_px: int,
    start: tuple[float, float],
    end: tuple[float, float],
) -> VisualIssue | None:
    """Return an issue when a selected line is fully outside the canvas."""

    if _point_inside(width_px, height_px, start) or _point_inside(width_px, height_px, end):
        return None
    return VisualIssue(
        "",
        str(Path("selected-line")),
        "line_annotation_image",
        "blocking",
        "selected_feature_missing",
        "Selected line is outside image bounds.",
        "Layout-to-image transform or crop bounds are inconsistent.",
        "Recompute transform bounds and keep selected endpoints visible.",
    )


def selected_point_issue(
    width_px: int,
    height_px: int,
    point: tuple[float, float],
) -> VisualIssue | None:
    """Return an issue when a selected point is outside the canvas."""

    if _point_inside(width_px, height_px, point):
        return None
    return VisualIssue(
        "",
        str(Path("selected-point")),
        "point_annotation_image",
        "blocking",
        "selected_feature_missing",
        "Selected point is outside image bounds.",
        "Layout-to-image transform or crop bounds are inconsistent.",
        "Expand crop bounds or correct point coordinate mapping.",
    )


def _point_inside(width_px: int, height_px: int, point: tuple[float, float]) -> bool:
    return 0 <= point[0] <= width_px and 0 <= point[1] <= height_px
