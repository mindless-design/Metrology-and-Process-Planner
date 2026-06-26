"""Generate manual review artifacts for advanced process geometry fixtures."""

from __future__ import annotations

import html
import json
import sys
from pathlib import Path
from typing import TYPE_CHECKING

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "python"))

if TYPE_CHECKING:
    from metrology_process_planner.domains.process import ProcessRecipe

CASES = (
    ("conformal_liner_narrow_trench", "conformal_liner_recipe", "physical_cross_section"),
    (
        "conformal_liner_pinch_off",
        "conformal_liner_recipe",
        "illustrative_process_cross_section",
    ),
    ("tapered_via_82deg", "tapered_etch_recipe", "illustrative_process_cross_section"),
    (
        "isotropic_undercut_bridge",
        "isotropic_undercut_recipe",
        "illustrative_process_cross_section",
    ),
    ("fib_full_stack_thin_liner", "conformal_liner_recipe", "fib_full_stack_compressed"),
    ("process_flow_conformal_step", "process_flow_recipe", "process_flow_frame"),
)


def main() -> None:
    """Write scene JSON, SVG previews, and an HTML index for advanced fixtures."""

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
    output_root = ROOT / "tests" / "output" / "advanced_geometry_gallery"
    output_root.mkdir(parents=True, exist_ok=True)
    renderer = SvgCrossSectionRenderer()
    rows: list[str] = []
    for case_id, recipe_id, profile_id in CASES:
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
                artifact_id=f"advanced-gallery:{case_id}",
            ),
        )
        rows.append(_row(case_id, recipe_id, profile_id, json_name, svg_name, scene.warnings))
    (output_root / "index.html").write_text(_page(rows) + "\n")


def _recipe(recipe_root: Path, recipe_id: str) -> ProcessRecipe:
    from metrology_process_planner.domains.process import ProcessRecipe

    return ProcessRecipe.from_dict(json.loads((recipe_root / f"{recipe_id}.json").read_text()))


def _row(
    case_id: str,
    recipe_id: str,
    profile_id: str,
    json_name: str,
    svg_name: str,
    warnings: tuple[str, ...],
) -> str:
    return (
        "<tr>"
        f"<td>{html.escape(case_id)}</td>"
        f"<td>{html.escape(recipe_id)}</td>"
        f"<td>{html.escape(profile_id)}</td>"
        f"<td>{html.escape(', '.join(warnings))}</td>"
        f"<td><a href=\"{html.escape(svg_name)}\">svg</a></td>"
        f"<td><a href=\"{html.escape(json_name)}\">scene json</a></td>"
        "</tr>"
    )


def _page(rows: list[str]) -> str:
    return (
        "<!doctype html><html><head><meta charset=\"utf-8\">"
        "<title>Advanced Process Geometry Gallery</title>"
        "<style>body{font-family:Arial,sans-serif;margin:24px}"
        "table{border-collapse:collapse;width:100%}"
        "td,th{border:1px solid #ccc;padding:6px;text-align:left}</style>"
        "</head><body><h1>Advanced Process Geometry Gallery</h1>"
        "<table><thead><tr><th>Case</th><th>Recipe</th><th>Profile</th>"
        "<th>Warnings</th><th>SVG</th><th>Scene</th></tr></thead><tbody>"
        + "".join(rows)
        + "</tbody></table></body></html>"
    )


if __name__ == "__main__":
    main()
