"""Generate process-render manifest items for the visual quality gallery."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from metrology_process_planner.domains.process import ProcessRecipe
from metrology_process_planner.testing.visual_quality import VisualManifestItem

PROCESS_CASES = (
    ("profilometry_surface_profile", "profilometry_surface_recipe", "profilometry_surface_profile"),
    ("ellipsometry_point_stack", "simple_stack_recipe", "point_stack_schematic"),
    ("fib_full_stack_compressed", "fib_full_stack_recipe", "fib_full_stack_compressed"),
    ("process_flow_frame", "process_flow_recipe", "process_flow_frame"),
    ("thin_conformal_liner", "conformal_liner_recipe", "illustrative_process_cross_section"),
    ("physical_cross_section", "simple_stack_recipe", "physical_cross_section"),
)


def process_items(root: Path, output_root: Path) -> list[VisualManifestItem]:
    """Return rendered process visual manifest items."""

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

    recipe_root = root / "tests" / "fixtures" / "recipes"
    renderer = SvgCrossSectionRenderer()
    items: list[VisualManifestItem] = []
    for visual_type, recipe_id, profile_id in PROCESS_CASES:
        recipe = _recipe(recipe_root, recipe_id)
        result = HybridCrossSectionSolver().solve(
            SolverInput(recipe, SolverOptions(x_min=0.0, x_max=10.0, sample_count=31))
        )
        profile = built_in_render_profile(profile_id)
        scene = build_cross_section_scene(
            result,
            profile,
            materials=recipe.materials,
            scene_id=visual_type,
        )
        scene_name = f"process/{visual_type}.scene.json"
        svg_name = f"process/{visual_type}.svg"
        _write_json(output_root / scene_name, scene_to_dict(scene))
        renderer.render(
            scene,
            CrossSectionOutputSpec(
                output_path=str(output_root / svg_name),
                artifact_id=f"process:{visual_type}",
            ),
        )
        items.append(_process_item(scene, visual_type, recipe_id, profile_id, svg_name, scene_name))
    return items


def _process_item(
    scene: Any,
    visual_type: str,
    recipe_id: str,
    profile_id: str,
    svg_name: str,
    scene_name: str,
) -> VisualManifestItem:
    metadata = {
        "golden_family": "render",
        "recipe_id": recipe_id,
        "render_mode_id": scene.render_mode_id,
        "render_profile": profile_id,
        "visual_type": visual_type,
    }
    return VisualManifestItem(
        artifact_id=f"process:{visual_type}",
        visual_type=visual_type,
        source_fixture=recipe_id,
        mode=scene.render_mode_id,
        render_profile=profile_id,
        image_path=svg_name,
        status="pending",
        warnings=scene.warnings,
        metadata_path=scene_name,
        source_artifact_id=f"process:{recipe_id}:{profile_id}",
        metadata=metadata,
    )


def _recipe(recipe_root: Path, recipe_id: str) -> ProcessRecipe:
    return ProcessRecipe.from_dict(json.loads((recipe_root / f"{recipe_id}.json").read_text()))


def _write_json(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, indent=2, sort_keys=True) + "\n", encoding="utf-8")
