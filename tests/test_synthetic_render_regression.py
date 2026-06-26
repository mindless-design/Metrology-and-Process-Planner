import json
import unittest
from typing import Any

from metrology_process_planner.domains.process import (
    HybridCrossSectionSolver,
    ProcessRecipe,
    SolverInput,
    SolverOptions,
)
from metrology_process_planner.rendering.cross_section import (
    build_cross_section_scene,
    built_in_render_profile,
    scene_to_dict,
)
from metrology_process_planner.rendering.cross_section.scene_models import CrossSectionSceneModel
from tests.synthetic_process_lab import GOLDEN_ROOT, RECIPE_ROOT, write_debug_json

RENDER_CASES = (
    ("simple_stack_recipe", "physical_cross_section"),
    ("conformal_liner_recipe", "illustrative_process_cross_section"),
    ("profilometry_surface_recipe", "profilometry_surface_profile"),
    ("fib_full_stack_recipe", "fib_full_stack_compressed"),
    ("process_flow_recipe", "process_flow_frame"),
)


class SyntheticRenderRegressionTests(unittest.TestCase):
    def test_render_scene_summaries_match_golden_snapshots(self) -> None:
        for recipe_id, profile_id in RENDER_CASES:
            with self.subTest(recipe_id=recipe_id, profile_id=profile_id):
                actual = _scene_summary(recipe_id, profile_id)
                expected = json.loads(
                    (GOLDEN_ROOT / "render" / f"{recipe_id}.{profile_id}.expected.json").read_text()
                )
                if actual != expected:
                    write_debug_json(f"{recipe_id}.{profile_id}.actual.render.json", actual)
                self.assertEqual(expected, actual)

    def test_scene_json_is_stable_and_serializable(self) -> None:
        scene = _build_scene("conformal_liner_recipe", "illustrative_process_cross_section")
        payload = scene_to_dict(scene)

        self.assertEqual("illustrative_process", payload["render_mode_id"])
        self.assertTrue(payload["material_shapes"])
        self.assertTrue(payload["labels"])

    def test_render_failures_have_explicit_warning_surface(self) -> None:
        empty_result = HybridCrossSectionSolver().solve(
            SolverInput(_load_recipe("simple_stack_recipe"), SolverOptions(sample_count=3))
        )
        profile = built_in_render_profile("physical_cross_section")
        scene = build_cross_section_scene(empty_result, profile, materials=())

        self.assertTrue(scene.material_shapes)
        self.assertIsInstance(scene.warnings, tuple)


def _scene_summary(recipe_id: str, profile_id: str) -> dict[str, Any]:
    scene = _build_scene(recipe_id, profile_id)
    material_counts: dict[str, int] = {}
    for shape in scene.material_shapes:
        material_counts[shape.material_id] = material_counts.get(shape.material_id, 0) + 1
    return {
        "recipe_id": recipe_id,
        "profile_id": profile_id,
        "render_mode_id": scene.render_mode_id,
        "shape_count": len(scene.material_shapes),
        "materials": dict(sorted(material_counts.items())),
        "label_count": len(scene.labels),
        "warnings": sorted(scene.warnings),
        "compression_enabled": scene.compression_metadata.enabled,
        "compressed_materials": sorted(scene.compression_metadata.affected_materials),
        "thin_layer_shape_count": sum(
            1 for shape in scene.material_shapes if shape.exaggerated_flag
        ),
    }


def _build_scene(recipe_id: str, profile_id: str) -> CrossSectionSceneModel:
    recipe = _load_recipe(recipe_id)
    result = HybridCrossSectionSolver().solve(
        SolverInput(recipe, SolverOptions(x_min=0.0, x_max=10.0, sample_count=31))
    )
    return build_cross_section_scene(
        result,
        built_in_render_profile(profile_id),
        materials=recipe.materials,
        scene_id=f"{recipe_id}.{profile_id}",
        title=recipe.name,
    )


def _load_recipe(recipe_id: str) -> ProcessRecipe:
    return ProcessRecipe.from_dict(json.loads((RECIPE_ROOT / f"{recipe_id}.json").read_text()))


if __name__ == "__main__":
    unittest.main()
