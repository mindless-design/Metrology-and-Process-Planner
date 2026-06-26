import json
import unittest
from pathlib import Path

from metrology_process_planner.domains.process import (
    HybridCrossSectionSolver,
    ProcessRecipe,
    ProcessStep,
    ProcessStepKind,
    SolverInput,
    SolverOptions,
    ThicknessSpec,
    validate_render_projection,
)
from metrology_process_planner.rendering.cross_section import (
    build_cross_section_scene,
    built_in_render_profile,
)

RECIPE_ROOT = Path("tests/fixtures/recipes")


class AdvancedGeometryKernelTests(unittest.TestCase):
    def test_conformal_liner_projection_carries_surface_growth_metadata(self) -> None:
        result = _solve("conformal_liner_recipe")
        projection = result.render_projections[0]
        codes = _codes(result)

        self.assertTrue(validate_render_projection(projection).passed)
        self.assertTrue(projection.conformal_layers)
        self.assertTrue(projection.pinch_off_regions)
        self.assertEqual("al2o3", projection.conformal_layers[0].material_id)
        self.assertTrue(projection.conformal_layers[0].thin_layer_flag)
        self.assertTrue(projection.thin_layer_hints["exaggeration_note_required"])
        self.assertIn("CONFORMAL_APPROXIMATION_USED", codes)
        self.assertIn("CONFORMAL_PINCH_OFF_DETECTED", codes)
        self.assertIn("CONFORMAL_VOID_OR_SEAM_DETECTED", codes)

    def test_tapered_etch_projection_carries_renderable_sloped_region(self) -> None:
        result = _solve("tapered_etch_recipe")
        projection = result.render_projections[0]
        tapered = projection.tapered_regions[0]

        self.assertTrue(projection.tapered_regions)
        self.assertLess(tapered.x_bottom_max - tapered.x_bottom_min,
                        tapered.x_top_max - tapered.x_top_min)
        self.assertEqual(4, len(tapered.polygon))
        self.assertIn("dielectric", tapered.target_materials)
        self.assertIn("TAPERED_PROFILE_APPROXIMATED", _codes(result))

    def test_isotropic_etch_projection_carries_undercut_region(self) -> None:
        result = _solve("isotropic_undercut_recipe")
        projection = result.render_projections[0]

        self.assertTrue(projection.undercut_regions)
        self.assertIn("sacrificial", projection.undercut_regions[0].target_materials)
        self.assertIn("ISOTROPIC_UNDERCUT_APPROXIMATED", _codes(result))

    def test_invalid_tapered_angle_is_blocking_diagnostic(self) -> None:
        recipe = _recipe("tapered_etch_recipe")
        bad_step = ProcessStep(
            "bad-angle",
            ProcessStepKind.TAPERED_ETCH,
            thickness=ThicknessSpec(10.0),
            target_material_ids=("dielectric",),
            parameters={"sidewall_angle_deg": 90.0},
        )
        recipe = ProcessRecipe(
            recipe.id,
            recipe.name,
            recipe.materials,
            recipe.steps[:2] + (bad_step,),
        )

        result = HybridCrossSectionSolver().solve(SolverInput(recipe))
        diagnostic = next(item for item in result.diagnostics
                          if item.code == "TAPERED_ETCH_INVALID_ANGLE")

        self.assertEqual("error", diagnostic.severity)
        self.assertFalse(diagnostic.output_usable)

    def test_scene_uses_projection_metadata_for_advanced_annotations(self) -> None:
        recipe = _recipe("conformal_liner_recipe")
        result = _solve_recipe(recipe)
        profile = built_in_render_profile("illustrative_process_cross_section")
        scene = build_cross_section_scene(result, profile, materials=recipe.materials)

        annotation_kinds = {item["kind"] for item in scene.annotations}
        highlight_kinds = {item["kind"] for item in scene.highlights}

        self.assertIn("conformal_layer", annotation_kinds)
        self.assertIn("pinch_off_warning", highlight_kinds)
        self.assertIn("RENDER_CONFORMAL_THIN_LAYER_HINT_PRESENT", scene.warnings)


def _solve(recipe_id: str):
    return _solve_recipe(_recipe(recipe_id))


def _solve_recipe(recipe: ProcessRecipe):
    return HybridCrossSectionSolver().solve(
        SolverInput(recipe, SolverOptions(x_min=0.0, x_max=10.0, sample_count=31))
    )


def _recipe(recipe_id: str) -> ProcessRecipe:
    return ProcessRecipe.from_dict(json.loads((RECIPE_ROOT / f"{recipe_id}.json").read_text()))


def _codes(result) -> set[str]:
    return {item.code for item in result.diagnostics}


if __name__ == "__main__":
    unittest.main()
