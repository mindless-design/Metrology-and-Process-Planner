"""Generate clarity-focused visual artifact review gallery."""

from __future__ import annotations

import html
import json
import sys
from pathlib import Path
from typing import TYPE_CHECKING, Any

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "python"))

if TYPE_CHECKING:
    from metrology_process_planner.domains.process import ProcessRecipe

PROCESS_CASES = (
    ("profilometry_surface_profile", "profilometry_surface_recipe", "profilometry_surface_profile"),
    ("ellipsometry_point_stack", "simple_stack_recipe", "point_stack_schematic"),
    ("fib_full_stack_compressed", "fib_full_stack_recipe", "fib_full_stack_compressed"),
    ("process_flow_frame", "process_flow_recipe", "process_flow_frame"),
    ("thin_conformal_liner", "conformal_liner_recipe", "illustrative_process_cross_section"),
    ("tapered_trench", "tapered_etch_recipe", "illustrative_process_cross_section"),
)


def main() -> None:
    """Write SVG previews, scene JSON, and an HTML index for clarity review."""

    from metrology_process_planner.domains.process import (
        HybridCrossSectionSolver,
        SolverInput,
        SolverOptions,
    )
    from metrology_process_planner.rendering.cross_section import (
        CrossSectionOutputSpec,
        SvgCrossSectionRenderer,
        build_cross_section_scene,
        built_in_render_profile,
        scene_to_dict,
    )

    recipe_root = ROOT / "tests" / "fixtures" / "recipes"
    output_root = ROOT / "tests" / "output" / "visual_polish_gallery"
    output_root.mkdir(parents=True, exist_ok=True)
    renderer = SvgCrossSectionRenderer()
    rows: list[str] = []
    for case_id, recipe_id, profile_id in PROCESS_CASES:
        recipe = _recipe(recipe_root, recipe_id)
        result = HybridCrossSectionSolver().solve(
            SolverInput(recipe, SolverOptions(x_min=0.0, x_max=10.0, sample_count=61))
        )
        profile = built_in_render_profile(profile_id)
        scene = build_cross_section_scene(
            result,
            profile,
            materials=recipe.materials,
            scene_id=case_id,
        )
        json_name = f"{case_id}.scene.json"
        svg_name = f"{case_id}.svg"
        (output_root / json_name).write_text(json.dumps(scene_to_dict(scene), indent=2) + "\n")
        renderer.render(
            scene,
            CrossSectionOutputSpec(
                output_path=str(output_root / svg_name),
                artifact_id=f"visual-polish:{case_id}",
                theme_id=profile.theme_id,
            ),
        )
        rows.append(_row(case_id, recipe_id, profile_id, svg_name, json_name, scene.warnings))
    rows.extend(_site_rows(output_root))
    (output_root / "index.html").write_text(_page(rows) + "\n")


def _recipe(recipe_root: Path, recipe_id: str) -> ProcessRecipe:
    from metrology_process_planner.domains.process import ProcessRecipe

    return ProcessRecipe.from_dict(json.loads((recipe_root / f"{recipe_id}.json").read_text()))


def _site_rows(output_root: Path) -> list[str]:
    from PIL import Image, ImageDraw
    from tests.capture_metadata_pipeline_fixtures import line_feature_capture, session_with_capture

    from metrology_process_planner.persistence.paths import SessionPaths
    from metrology_process_planner.workflows.artifacts.visual_capture_generator import (
        generate_labeled_site_artifact,
        generate_site_overview_artifact,
    )

    _write_site_source_image(output_root, Image, ImageDraw)
    capture = line_feature_capture()
    paths = SessionPaths.for_folder(output_root)
    session = generate_labeled_site_artifact(session_with_capture(capture), capture, paths)
    session = generate_site_overview_artifact(session, session.captures[0], paths)
    rows: list[str] = []
    for role, case_id in (
        ("site_image_labeled", "labeled_site_image"),
        ("site_overview_image", "site_overview_with_label"),
    ):
        artifact_id = dict(session.captures[0].artifact_refs or {})[role]
        artifact = dict(session.artifacts or {})[artifact_id]
        rows.append(_row(case_id, "capture_site", role, artifact.relative_path, "", ()))
    return rows


def _write_site_source_image(output_root: Path, image_type: Any, draw_type: Any) -> None:
    image_dir = output_root / "images"
    image_dir.mkdir(parents=True, exist_ok=True)
    image = image_type.new("RGB", (1024, 768), "#101827")
    draw = draw_type.Draw(image)
    draw.rectangle((170, 150, 850, 610), outline="#475569", width=4)
    for offset, color in ((0, "#1e293b"), (38, "#172033"), (76, "#111827")):
        draw.rectangle((190 + offset, 170 + offset, 830 - offset, 590 - offset), outline=color)
    draw.line((250, 530, 780, 220), fill="#67e8f9", width=8)
    draw.ellipse((240, 520, 260, 540), fill="#fbbf24")
    draw.ellipse((770, 210, 790, 230), fill="#fbbf24")
    draw.text((180, 120), "Synthetic process site", fill="#f8fafc")
    image.save(image_dir / "cap-001.png")
    nested = image_dir / "images"
    nested.mkdir(parents=True, exist_ok=True)
    image.save(nested / "cap-001.png")


def _row(
    case_id: str,
    source_id: str,
    profile_id: str,
    svg_name: str,
    json_name: str,
    warnings: tuple[str, ...],
) -> str:
    scene_link = f"<a href=\"{html.escape(json_name)}\">scene json</a>" if json_name else ""
    return (
        "<tr>"
        f"<td>{html.escape(case_id)}</td>"
        f"<td>{html.escape(source_id)}</td>"
        f"<td>{html.escape(profile_id)}</td>"
        f"<td>{html.escape(', '.join(warnings))}</td>"
        f"<td><a href=\"{html.escape(svg_name)}\">svg</a></td>"
        f"<td>{scene_link}</td>"
        "</tr>"
        "<tr>"
        f"<td colspan=\"6\"><iframe src=\"{html.escape(svg_name)}\" "
        "loading=\"lazy\"></iframe></td>"
        "</tr>"
    )


def _page(rows: list[str]) -> str:
    return (
        "<!doctype html><html><head><meta charset=\"utf-8\">"
        "<title>Process Output Visual Polish Gallery</title>"
        "<style>"
        "body{font-family:Arial,sans-serif;margin:24px;background:#0b1120;color:#f8fafc}"
        "a{color:#67e8f9}table{border-collapse:collapse;width:100%}"
        "td,th{border:1px solid #334155;padding:8px;text-align:left;vertical-align:top}"
        "th{background:#111827;color:#bae6fd}"
        "iframe{width:100%;height:520px;border:1px solid #38bdf8;background:#0b1120}"
        "</style>"
        "</head><body><h1>Process Output Visual Polish Gallery</h1>"
        "<table><thead><tr><th>Case</th><th>Source</th><th>Profile/Role</th>"
        "<th>Warnings</th><th>SVG</th><th>Scene</th></tr></thead><tbody>"
        + "".join(rows)
        + "</tbody></table></body></html>"
    )


if __name__ == "__main__":
    main()
