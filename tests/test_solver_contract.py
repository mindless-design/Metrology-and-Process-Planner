"""Contract tests for process solver outputs and renderer handoff."""

from __future__ import annotations

import ast
import unittest
from pathlib import Path

from metrology_process_planner.domains.process import (
    HybridCrossSectionSolver,
    MaskInterval,
    MaterialInterval,
    ProcessStep,
    ProcessStepKind,
    ProcessWindow,
    SolverInput,
    SolverOptions,
    StackColumn,
    StackGeometry2D,
    StackInvariantChecker,
    ThicknessSpec,
    validate_render_projection,
    validate_solver_input,
)
from metrology_process_planner.solver.geometry_models import (
    MaterialRegion,
    RenderProjection,
    SurfaceProfile,
)
from tests.hybrid_solver_fixtures import _blanket, _recipe, _substrate

PROCESS_ROOT = Path("python/metrology_process_planner/domains/process")
FORBIDDEN_IMPORTS = ("pya", "qt", "PyQt", "PySide")
FORBIDDEN_RENDER_CALLS = ("render", "save_image", "export_png", "export_svg")


class SolverContractTests(unittest.TestCase):
    def test_solver_core_import_boundary_has_no_klayout_or_qt(self) -> None:
        for path in PROCESS_ROOT.glob("*.py"):
            tree = ast.parse(path.read_text())
            imports = _imports(tree)
            self.assertFalse(
                [item for item in imports if any(token in item for token in FORBIDDEN_IMPORTS)],
                path.as_posix(),
            )

    def test_solver_core_does_not_call_renderer_or_image_export(self) -> None:
        for path in PROCESS_ROOT.glob("*.py"):
            tree = ast.parse(path.read_text())
            calls = [node.func.attr for node in ast.walk(tree) if isinstance(node, ast.Call)
                     and isinstance(node.func, ast.Attribute)]
            self.assertFalse(set(calls).intersection(FORBIDDEN_RENDER_CALLS), path.as_posix())

    def test_solver_result_populates_render_ready_contract_fields(self) -> None:
        result = HybridCrossSectionSolver().solve(
            SolverInput(_recipe(_substrate(), _blanket("oxide", 0.2)))
        )

        self.assertEqual("hybrid_cross_section_solver", result.solver_id)
        self.assertEqual("sampled_geometry", result.backend_id)
        self.assertEqual("fixture", result.recipe_id)
        self.assertTrue(result.input_hash)
        self.assertIsNotNone(result.final_stack)
        self.assertTrue(result.render_projections)
        self.assertTrue(result.material_metadata)
        self.assertTrue(validate_render_projection(result.render_projections[0]).passed)

    def test_input_validation_reports_invalid_recipe_parts(self) -> None:
        recipe = _recipe(
            _substrate(),
            ProcessStep(
                "bad",
                ProcessStepKind.PATTERNED_DEPOSITION,
                "missing",
                ThicknessSpec(-1.0),
                mask_intervals=(MaskInterval(1.0, 1.0),),
            ),
        )

        codes = {item.code for item in validate_solver_input(SolverInput(recipe))}

        self.assertIn("MISSING_LAYER", codes)
        self.assertIn("INVALID_THICKNESS", codes)
        self.assertIn("EMPTY_MASK", codes)

    def test_invalid_process_window_is_structured_diagnostic(self) -> None:
        recipe = _recipe(_substrate())
        recipe = type(recipe)(recipe.id, recipe.name, recipe.materials, recipe.steps,
                              (ProcessWindow("bad", 2.0, 1.0, 3.0),))

        codes = {item.code for item in validate_solver_input(SolverInput(recipe))}

        self.assertIn("INVALID_PROCESS_WINDOW", codes)

    def test_invariant_checker_catches_zero_thickness_and_unknown_material(self) -> None:
        stack = StackGeometry2D((StackColumn(0.0, (MaterialInterval("ghost", 0.0, 0.0),)),))

        result = StackInvariantChecker({"si"}).check_stack_model(stack, "bad")

        self.assertFalse(result.passed)
        self.assertEqual({"STACK_INVARIANT_VIOLATION"}, {item.code for item in result.diagnostics})

    def test_surface_profile_matches_stack_tops(self) -> None:
        stack = StackGeometry2D((StackColumn(0.0, (MaterialInterval("si", 0.0, 1.0),)),))

        result = StackInvariantChecker({"si"}).check_surface_profile(
            SurfaceProfile(((0.0, 2.0),)),
            stack,
            "surface",
        )

        self.assertFalse(result.passed)

    def test_render_projection_validation_catches_missing_units_and_materials(self) -> None:
        projection = RenderProjection(
            (MaterialRegion("oxide", 0.0, 1.0, 0.0, 1.0),),
            SurfaceProfile(((0.0, 1.0),)),
            ("oxide",),
            units="",
            materials=(),
        )

        result = validate_render_projection(projection)

        self.assertFalse(result.passed)
        self.assertIn("RENDER_PROJECTION_INCOMPLETE", {item.code for item in result.diagnostics})

    def test_strict_mode_validates_frames_and_projection(self) -> None:
        result = HybridCrossSectionSolver().solve(
            SolverInput(_recipe(_substrate()), SolverOptions(sample_count=11, strict_mode=True))
        )

        self.assertFalse(
            [item for item in result.diagnostics if item.code == "STACK_INVARIANT_VIOLATION"]
        )
        self.assertTrue(result.render_projections)

    def test_unchanged_frames_emit_only_when_requested(self) -> None:
        recipe = _recipe(_substrate(), ProcessStep("note", ProcessStepKind.ANNOTATION_ONLY))
        normal = HybridCrossSectionSolver().solve(
            SolverInput(recipe, SolverOptions(sample_count=11))
        )

        self.assertEqual(["substrate", "note"], [frame.step_id for frame in normal.frames])
        self.assertFalse(normal.frames[-1].changed_from_previous)


def _imports(tree: ast.AST) -> set[str]:
    names: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            names.update(alias.name for alias in node.names)
        elif isinstance(node, ast.ImportFrom) and node.module is not None:
            names.add(node.module)
    return names


if __name__ == "__main__":
    unittest.main()
