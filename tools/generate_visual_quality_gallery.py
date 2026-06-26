"""Generate the visual review gallery, manifest, and issue inventory."""

from __future__ import annotations

import html
import json
import shutil
import sys
from pathlib import Path
from typing import TYPE_CHECKING, Any

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "python"))

if TYPE_CHECKING:
    from metrology_process_planner.testing.visual_quality import VisualManifestItem


def main() -> None:
    """Write review-ready visuals and quality reports."""

    from metrology_process_planner.testing.visual_quality import evaluate_visual_item
    from tools.visual_quality_gallery_items import capture_items, process_items

    output_root = ROOT / "tests" / "output" / "visual_review_gallery"
    if output_root.exists():
        shutil.rmtree(output_root)
    output_root.mkdir(parents=True, exist_ok=True)
    manifest = [*process_items(ROOT, output_root), *capture_items(output_root)]
    issues = [
        issue
        for item in manifest
        for issue in evaluate_visual_item(output_root, item)
    ]
    manifest = [_with_status(output_root, item) for item in manifest]
    _write_json(output_root / "manifest.json", [item.to_dict() for item in manifest])
    _write_json(output_root / "visual_issues.json", [issue.to_dict() for issue in issues])
    (output_root / "index.html").write_text(_html_page(manifest, issues), encoding="utf-8")


def _with_status(root: Path, item: VisualManifestItem) -> VisualManifestItem:
    from dataclasses import replace

    from metrology_process_planner.testing.visual_quality import evaluate_visual_item, visual_status

    return replace(item, status=visual_status(evaluate_visual_item(root, item)))


def _html_page(manifest: list[VisualManifestItem], issues: list[Any]) -> str:
    issue_counts = _issue_counts(issues)
    rows = "".join(_row(item, issue_counts.get(item.artifact_id, 0)) for item in manifest)
    return (
        "<!doctype html><html><head><meta charset=\"utf-8\">"
        "<title>Process Planner Visual Review Gallery</title>"
        "<style>body{font-family:Arial,sans-serif;margin:24px;color:#0f172a}"
        "table{border-collapse:collapse;width:100%}td,th{border:1px solid #cbd5e1;"
        "padding:6px;text-align:left;vertical-align:top}img{max-width:360px;max-height:220px}"
        ".pass{color:#166534}.needs_review,.warning{color:#92400e}.blocking{color:#991b1b}"
        "</style></head><body><h1>Process Planner Visual Review Gallery</h1>"
        "<p><a href=\"manifest.json\">manifest.json</a> "
        "<a href=\"visual_issues.json\">visual_issues.json</a></p>"
        "<table><thead><tr><th>Preview</th><th>Visual</th><th>Fixture</th><th>Profile</th>"
        "<th>Status</th><th>Warnings</th><th>Metadata</th></tr></thead><tbody>"
        f"{rows}</tbody></table></body></html>"
    )


def _row(item: VisualManifestItem, issue_count: int) -> str:
    metadata = (
        f'<a href="{html.escape(item.metadata_path)}">scene json</a>'
        if item.metadata_path else ""
    )
    warning_text = ", ".join(item.warnings)
    return (
        "<tr>"
        f'<td><a href="{html.escape(item.image_path)}"><img src="{html.escape(item.image_path)}">'
        "</a></td>"
        f"<td>{html.escape(item.visual_type)}<br>{html.escape(item.mode)}</td>"
        f"<td>{html.escape(item.source_fixture)}</td>"
        f"<td>{html.escape(item.render_profile)}</td>"
        f'<td class="{html.escape(item.status)}">{html.escape(item.status)}'
        f"<br>{issue_count} issues</td>"
        f"<td>{html.escape(warning_text)}</td>"
        f"<td>{metadata}</td>"
        "</tr>"
    )


def _issue_counts(issues: list[Any]) -> dict[str, int]:
    counts: dict[str, int] = {}
    for issue in issues:
        artifact_id = str(issue.issue_id).split(":VIS-", 1)[0]
        counts[artifact_id] = counts.get(artifact_id, 0) + 1
    return counts


def _write_json(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, indent=2, sort_keys=True) + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()
