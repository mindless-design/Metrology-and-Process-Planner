"""Visual review issue models and lightweight artifact checks."""

from __future__ import annotations

import json
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any

from metrology_process_planner.testing.visual_quality_geometry import (
    selected_line_issue,
    selected_point_issue,
)
from metrology_process_planner.testing.visual_quality_models import VisualIssue
from metrology_process_planner.testing.visual_quality_svg import evaluate_svg

ISSUE_SEVERITY_ORDER = {"blocking": 0, "major": 1, "minor": 2, "cosmetic": 3}
__all__ = [
    "VisualManifestItem",
    "VisualIssue",
    "evaluate_image_path",
    "evaluate_scene_metadata",
    "evaluate_visual_item",
    "overlapping_label_pairs",
    "selected_line_issue",
    "selected_point_issue",
    "visual_status",
]


@dataclass(frozen=True)
class VisualManifestItem:
    """One generated visual review gallery item."""

    artifact_id: str
    visual_type: str
    source_fixture: str
    mode: str
    render_profile: str
    image_path: str
    status: str
    warnings: tuple[str, ...] = ()
    metadata_path: str = ""
    source_artifact_id: str = ""
    capture_id: str = ""
    comparison_status: str = "not_configured"
    comparison_path: str = ""
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        """Return JSON-compatible manifest data."""

        data = asdict(self)
        data["warnings"] = list(self.warnings)
        data["output_path"] = self.image_path
        return data


def evaluate_visual_item(root: Path, item: VisualManifestItem) -> tuple[VisualIssue, ...]:
    """Evaluate one manifest item using available SVG/scene checks."""

    issues: list[VisualIssue] = []
    visual_path = root / item.image_path
    issues.extend(evaluate_image_path(visual_path, item.visual_type))
    if item.metadata_path:
        issues.extend(evaluate_scene_metadata(root / item.metadata_path, item.visual_type))
    return _renumber(item, issues)


def evaluate_image_path(path: Path, visual_type: str) -> tuple[VisualIssue, ...]:
    """Evaluate file presence, dimensions, drawable content, and text bounds."""

    if not path.exists():
        return (
            _issue(path, visual_type, "blocking", "missing_artifact",
                   "Visual artifact was not generated.",
                   "Generator did not write the expected file.",
                   "Keep missing outputs as issue records and fix generator routing."),
        )
    if path.suffix.lower() != ".svg":
        return _evaluate_non_svg(path, visual_type)
    return evaluate_svg(path, visual_type)


def evaluate_scene_metadata(path: Path, visual_type: str) -> tuple[VisualIssue, ...]:
    """Evaluate backend-independent scene metadata attached to a visual."""

    if not path.exists():
        return ()
    data = json.loads(path.read_text(encoding="utf-8"))
    issues: list[VisualIssue] = []
    if data.get("material_shapes") and not data.get("legend", {}).get("entries"):
        issues.append(_issue(path, visual_type, "major", "legend_missing",
                             "Scene has visible materials but no legend entries.",
                             "Scene assembly did not populate legend metadata.",
                             "Build legend entries from visible material shapes."))
    labels = tuple(dict(item) for item in data.get("labels", ()))
    for left, right in overlapping_label_pairs(labels):
        issues.append(_issue(path, visual_type, "major", "label_collision",
                             f"Labels overlap: {left} and {right}.",
                             "Label placement accepted intersecting boxes.",
                             "Move one label to a leader/callout lane or legend fallback."))
    if _requires_compression_note(data, visual_type):
        notes = " ".join(data.get("compression_metadata", {}).get("notes", ()))
        if "compress" not in notes.lower():
            issues.append(_issue(path, visual_type, "major", "compression_unclear",
                                 "Compressed scene lacks an explanatory note.",
                                 "Compression metadata did not carry user-facing notes.",
                                 "Add compression notes and render them in the SVG."))
    if _requires_thin_layer_callout(data, visual_type) and not _has_thin_layer_callout(data):
        issues.append(_issue(path, visual_type, "major", "thin_layer_invisible",
                             "Thin-layer scene lacks callout metadata.",
                             "Thin critical materials were not promoted to callouts.",
                             "Use leader/callout fallback for exaggerated thin layers."))
    return tuple(issues)


def visual_status(issues: tuple[VisualIssue, ...]) -> str:
    """Return gallery status for a visual based on issue severity."""

    severities = {issue.severity for issue in issues if issue.status == "open"}
    if "blocking" in severities:
        return "blocking"
    if "major" in severities:
        return "needs_review"
    if severities:
        return "warning"
    return "pass"


def overlapping_label_pairs(labels: tuple[dict[str, Any], ...]) -> tuple[tuple[str, str], ...]:
    """Return label ids whose bounding boxes overlap."""

    pairs: list[tuple[str, str]] = []
    boxes = [
        (str(label.get("label_id") or label.get("target_id")), tuple(label.get("bounding_box", ())))
        for label in labels
        if label.get("placement_type") != "legend_only"
    ]
    for index, (left_id, left_box) in enumerate(boxes):
        for right_id, right_box in boxes[index + 1:]:
            if _overlaps(left_box, right_box):
                pairs.append((left_id, right_id))
    return tuple(pairs)


def _evaluate_non_svg(path: Path, visual_type: str) -> tuple[VisualIssue, ...]:
    if path.stat().st_size <= 0:
        return (_issue(path, visual_type, "blocking", "blank_image",
                       "Image file is empty.", "Exporter wrote zero bytes.",
                       "Fail export or regenerate the source image."),)
    return ()


def _requires_compression_note(data: dict[str, Any], visual_type: str) -> bool:
    return "fib" in visual_type or data.get("compression_metadata", {}).get("enabled", False)


def _requires_thin_layer_callout(data: dict[str, Any], visual_type: str) -> bool:
    return "thin" in visual_type or any(
        bool(shape.get("thin_layer_flag") or shape.get("exaggerated_flag"))
        for shape in data.get("material_shapes", ())
    )


def _has_thin_layer_callout(data: dict[str, Any]) -> bool:
    if data.get("callouts"):
        return True
    return any(
        label.get("placement_type") in {"leader", "callout"}
        for label in data.get("labels", ())
    )


def _renumber(
    item: VisualManifestItem,
    issues: list[VisualIssue],
) -> tuple[VisualIssue, ...]:
    return tuple(
        VisualIssue(
            f"{item.artifact_id}:VIS-{index:03d}",
            issue.visual_path,
            issue.visual_type,
            issue.severity,
            issue.category,
            issue.description,
            issue.likely_cause,
            issue.recommended_fix,
            issue.status,
        )
        for index, issue in enumerate(issues, 1)
    )


def _issue(
    path: Path,
    visual_type: str,
    severity: str,
    category: str,
    description: str,
    likely_cause: str,
    recommended_fix: str,
) -> VisualIssue:
    return VisualIssue("", str(path), visual_type, severity, category, description,
                       likely_cause, recommended_fix)


def _overlaps(a: tuple[Any, ...], b: tuple[Any, ...]) -> bool:
    if len(a) != 4 or len(b) != 4:
        return False
    ax, ay, aw, ah = (float(value) for value in a)
    bx, by, bw, bh = (float(value) for value in b)
    return ax < bx + bw and ax + aw > bx and ay < by + bh and ay + ah > by
