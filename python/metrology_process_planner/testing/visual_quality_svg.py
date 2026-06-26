"""SVG-specific checks for generated visual artifacts."""

from __future__ import annotations

import time
import xml.etree.ElementTree as ET
from pathlib import Path
from urllib.parse import urlparse

from metrology_process_planner.testing.visual_quality_models import VisualIssue

SVG_NS = "{http://www.w3.org/2000/svg}"


def evaluate_svg(path: Path, visual_type: str) -> tuple[VisualIssue, ...]:
    """Evaluate SVG dimensions, text placement, drawable content, and hrefs."""

    root = ET.fromstring(_read_svg_text(path))
    width = _numeric(root.get("width"))
    height = _numeric(root.get("height"))
    left, top, right, bottom = _svg_view_bounds(root, width, height)
    issues: list[VisualIssue] = []
    issues.extend(_svg_canvas_issues(path, visual_type, root, width, height))
    issues.extend(_svg_text_issues(path, visual_type, root, (left, top, right, bottom)))
    issues.extend(_svg_image_reference_issues(path, visual_type, root))
    return tuple(issues)


def _svg_canvas_issues(
    path: Path,
    visual_type: str,
    root: ET.Element,
    width: float,
    height: float,
) -> list[VisualIssue]:
    issues: list[VisualIssue] = []
    if width <= 1 or height <= 1:
        issues.append(_issue(path, visual_type, "blocking", "wrong_scale",
                             "SVG has invalid dimensions.",
                             "Canvas size was missing or collapsed.",
                             "Export with explicit nonzero width and height."))
    if _drawable_count(root) <= 1:
        issues.append(_issue(path, visual_type, "blocking", "blank_image",
                             "SVG has no meaningful drawable content.",
                             "Renderer emitted only a background or empty scene.",
                             "Ensure the selected scene contains primitives before export."))
    return issues


def _svg_text_issues(
    path: Path,
    visual_type: str,
    root: ET.Element,
    bounds: tuple[float, float, float, float],
) -> list[VisualIssue]:
    left, top, right, bottom = bounds
    issues: list[VisualIssue] = []
    for text in root.iter(f"{SVG_NS}text"):
        x = _numeric(text.get("x"))
        y = _numeric(text.get("y"))
        if x < left or y < top or x > right or y > bottom:
            issues.append(_issue(path, visual_type, "major", "text_clipped",
                                 f"Text is outside canvas: {''.join(text.itertext()).strip()}",
                                 "Label placement did not fit within export bounds.",
                                 "Include label extents in bounds or use a fallback lane."))
    return issues


def _svg_image_reference_issues(
    path: Path,
    visual_type: str,
    root: ET.Element,
) -> list[VisualIssue]:
    issues: list[VisualIssue] = []
    for image in root.iter(f"{SVG_NS}image"):
        href = image.get("href") or image.get("{http://www.w3.org/1999/xlink}href") or ""
        if _missing_local_href(path, href):
            issues.append(_issue(path, visual_type, "major", "image_reference_missing",
                                 f"Image layer reference is missing: {href}",
                                 "SVG image href is not relative to the SVG artifact location.",
                                 "Write SVG-local hrefs while keeping canonical artifact paths."))
    return issues


def _issue(
    path: Path,
    visual_type: str,
    severity: str,
    category: str,
    description: str,
    likely_cause: str,
    recommended_fix: str,
) -> VisualIssue:
    return VisualIssue(
        "",
        str(path),
        visual_type,
        severity,
        category,
        description,
        likely_cause,
        recommended_fix,
    )


def _drawable_count(root: ET.Element) -> int:
    tags = {"rect", "image", "line", "ellipse", "polyline", "polygon", "path", "text"}
    return sum(1 for item in root.iter() if item.tag.removeprefix(SVG_NS) in tags)


def _svg_view_bounds(
    root: ET.Element,
    width: float,
    height: float,
) -> tuple[float, float, float, float]:
    view_box = str(root.get("viewBox") or "").split()
    if len(view_box) != 4:
        return (0.0, 0.0, width, height)
    left, top, box_width, box_height = (_numeric(item) for item in view_box)
    return (left, top, left + box_width, top + box_height)


def _missing_local_href(svg_path: Path, href: str) -> bool:
    if not href or href.startswith("data:"):
        return False
    parsed = urlparse(href)
    if parsed.scheme and parsed.scheme != "file":
        return False
    target = Path(parsed.path) if parsed.scheme == "file" else svg_path.parent / href
    return not target.exists()


def _numeric(value: object) -> float:
    if value is None:
        return 0.0
    text = str(value).strip().removesuffix("px")
    try:
        return float(text)
    except ValueError:
        return 0.0


def _read_svg_text(path: Path) -> str:
    for _attempt in range(5):
        try:
            return path.read_text(encoding="utf-8")
        except PermissionError:
            time.sleep(0.2)
    return path.read_text(encoding="utf-8")
