"""Generate a manual HTML preview gallery for synthetic render scenes."""

from __future__ import annotations

import html
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "python"))


def main() -> None:
    """Write a lightweight render-scene gallery to tests/output/render_gallery."""

    from tests.test_synthetic_render_regression import RENDER_CASES, _build_scene

    from metrology_process_planner.rendering.cross_section import scene_to_dict

    output_root = ROOT / "tests" / "output" / "render_gallery"
    output_root.mkdir(parents=True, exist_ok=True)
    rows: list[str] = []
    for recipe_id, profile_id in RENDER_CASES:
        scene = _build_scene(recipe_id, profile_id)
        json_name = f"{recipe_id}.{profile_id}.scene.json"
        (output_root / json_name).write_text(json.dumps(scene_to_dict(scene), indent=2) + "\n")
        rows.append(
            "<tr>"
            f"<td>{html.escape(recipe_id)}</td>"
            f"<td>{html.escape(profile_id)}</td>"
            f"<td>{len(scene.material_shapes)}</td>"
            f"<td>{len(scene.labels)}</td>"
            f"<td>{html.escape(', '.join(scene.warnings))}</td>"
            f"<td><a href=\"{html.escape(json_name)}\">scene json</a></td>"
            "</tr>"
        )
    page = (
        "<!doctype html><html><head><meta charset=\"utf-8\">"
        "<title>Process Planner Render Gallery</title>"
        "<style>body{font-family:Arial,sans-serif;margin:24px}"
        "table{border-collapse:collapse;width:100%}"
        "td,th{border:1px solid #ccc;padding:6px;text-align:left}</style>"
        "</head><body><h1>Process Planner Render Gallery</h1>"
        "<table><thead><tr><th>Recipe</th><th>Profile</th><th>Shapes</th>"
        "<th>Labels</th><th>Warnings</th><th>Artifact</th></tr></thead><tbody>"
        + "".join(rows)
        + "</tbody></table></body></html>"
    )
    (output_root / "index.html").write_text(page + "\n")


if __name__ == "__main__":
    main()
