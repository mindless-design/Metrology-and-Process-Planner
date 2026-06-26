import json
import unittest
from typing import Any

from metrology_process_planner.domains.process import (
    HybridCrossSectionSolver,
    ProcessRecipe,
    SolverInput,
    SolverOptions,
)
from tests.synthetic_process_lab import GOLDEN_ROOT, RECIPE_ROOT, write_debug_json

EXECUTABLE_RECIPES = (
    "simple_stack_recipe",
    "patterned_deposition_recipe",
    "directional_etch_recipe",
    "tapered_etch_recipe",
    "isotropic_undercut_recipe",
    "conformal_liner_recipe",
    "cmp_planarization_recipe",
    "profilometry_surface_recipe",
    "fib_full_stack_recipe",
    "process_flow_recipe",
)


class SyntheticSolverRegressionTests(unittest.TestCase):
    def test_all_required_golden_recipes_exist_and_validate(self) -> None:
        for recipe_id in EXECUTABLE_RECIPES:
            with self.subTest(recipe_id=recipe_id):
                recipe = _load_recipe(recipe_id)

                self.assertEqual(recipe_id, recipe.id)
                self.assertFalse(recipe.validate())
                self.assertTrue((recipe.metadata or {}).get("fixture_target"))
                self.assertTrue(_accuracy_envelope(recipe))

    def test_solver_summaries_match_golden_snapshots(self) -> None:
        for recipe_id in (
            "simple_stack_recipe",
            "conformal_liner_recipe",
            "tapered_etch_recipe",
            "profilometry_surface_recipe",
            "fib_full_stack_recipe",
        ):
            with self.subTest(recipe_id=recipe_id):
                actual = _solver_summary(recipe_id)
                expected = _load_golden("solver", f"{recipe_id}.expected.json")
                if actual != expected:
                    write_debug_json(f"{recipe_id}.actual.solver.json", actual)
                self.assertEqual(expected, actual)

    def test_process_window_variants_are_deterministic(self) -> None:
        recipe = _load_recipe("process_flow_recipe")
        solver_input = SolverInput(recipe, SolverOptions(sample_count=31, x_min=0.0, x_max=10.0))

        variants = HybridCrossSectionSolver().solve_variants(solver_input)

        self.assertEqual(
            ("liner_thickness:lower", "liner_thickness:target", "liner_thickness:upper"),
            tuple(variant.variant_label for variant in variants),
        )
        self.assertEqual(
            [_stack_signature(variant) for variant in variants],
            [_stack_signature(variant) for variant in variants],
        )


def _load_recipe(recipe_id: str) -> ProcessRecipe:
    data = json.loads((RECIPE_ROOT / f"{recipe_id}.json").read_text())
    return ProcessRecipe.from_dict(data)


def _accuracy_envelope(recipe: ProcessRecipe) -> bool:
    envelope = dict((recipe.metadata or {}).get("accuracy_envelope") or {})
    required = ("model", "claim", "covers", "excludes")
    return all(envelope.get(key) for key in required)


def _solver_summary(recipe_id: str) -> dict[str, Any]:
    recipe = _load_recipe(recipe_id)
    result = HybridCrossSectionSolver().solve(
        SolverInput(
            recipe,
            SolverOptions(
                x_min=0.0,
                x_max=10.0,
                sample_count=31,
                point_sample_xs=(1.0, 5.0, 9.0),
                cutline_x_min=0.0,
                cutline_x_max=10.0,
            ),
        )
    )
    final = result.frames[-1]
    top_surface = [round(column.top, 3) for column in final.profile.columns]
    return {
        "recipe_id": recipe_id,
        "frame_count": len(result.frames),
        "final_step": final.step_id,
        "materials": sorted(
            {item.material_id for column in final.profile.columns for item in column.intervals}
        ),
        "diagnostics": sorted(
            {item.code for item in result.diagnostics if item.code != "STACK_INVARIANT_VIOLATION"}
        ),
        "stack_signature": _stack_signature(result),
        "top_min": min(top_surface),
        "top_max": max(top_surface),
        "point_sample_count": len(result.point_samples),
        "cutline_sample_count": len(result.cutline_samples),
    }


def _stack_signature(result: Any) -> list[list[object]]:
    return [
        [round(column.x, 3), [interval.material_id for interval in column.intervals]]
        for column in result.frames[-1].profile.columns
    ]


def _load_golden(category: str, name: str) -> dict[str, Any]:
    return dict(json.loads((GOLDEN_ROOT / category / name).read_text()))


if __name__ == "__main__":
    unittest.main()
