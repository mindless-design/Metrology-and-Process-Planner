"""Pure-Python fixtures for the hybrid cross-section solver."""

from __future__ import annotations

import unittest

from metrology_process_planner.domains.process import (
    ConformalProfile,
    EtchProfile,
    HybridCrossSectionSolver,
    MaskInterval,
    MaskPolarity,
    PlanarizationProfile,
    ProcessRecipe,
    ProcessStep,
    ProcessStepKind,
    SolverInput,
    SolverOptions,
    ThicknessSpec,
    build_recipe_to_pyxs_plan,
)
from tests.hybrid_solver_fixtures import (
    _blanket,
    _cmp,
    _codes,
    _patterned,
    _recipe,
    _solve,
    _stack,
    _substrate,
    _top,
    _window,
)


class HybridCrossSectionSolverTests(unittest.TestCase):
    def test_simple_patterned_deposition(self) -> None:
        result = _solve(_recipe(_substrate(), _patterned("oxide", (MaskInterval(2, 4),))))
        inside = _stack(result, 3.0)
        outside = _stack(result, 1.0)
        self.assertEqual(inside[-1].material_id, "oxide")
        self.assertEqual(outside[-1].material_id, "si")

    def test_inverted_mask_deposition(self) -> None:
        step = _patterned("oxide", (MaskInterval(2, 4),), MaskPolarity.INVERTED)
        result = _solve(_recipe(_substrate(), step))
        self.assertEqual(_stack(result, 3.0)[-1].material_id, "si")
        self.assertEqual(_stack(result, 1.0)[-1].material_id, "oxide")

    def test_conformal_liner_in_trench(self) -> None:
        conformal = ProcessStep(
            "liner",
            ProcessStepKind.CONFORMAL_DEPOSITION,
            material_id="nitride",
            thickness=ThicknessSpec(0.2),
            conformal_profile=ConformalProfile(1.0, 1.0, 1.0),
        )
        result = _solve(_recipe(_substrate(), _patterned("oxide", _banks()), conformal))
        self.assertIn("CONFORMAL_APPROXIMATION_USED", _codes(result))
        self.assertTrue(any(item.material_id == "nitride" for item in _stack(result, 5.0)))

    def test_narrow_gap_conformal_pinch_off(self) -> None:
        step = ProcessStep(
            "liner",
            ProcessStepKind.CONFORMAL_DEPOSITION,
            material_id="nitride",
            thickness=ThicknessSpec(0.4),
            mask_intervals=(MaskInterval(0.0, 0.6),),
        )
        result = _solve(_recipe(_substrate(), step))
        self.assertIn("CONFORMAL_PINCH_OFF", _codes(result))

    def test_directional_etch_with_blocker(self) -> None:
        blocker = ProcessStep(
            "blocker",
            ProcessStepKind.BLANKET_DEPOSITION,
            "nitride",
            ThicknessSpec(0.2),
        )
        etch = ProcessStep(
            "etch",
            ProcessStepKind.DIRECTIONAL_ETCH,
            thickness=ThicknessSpec(1.0),
            target_material_ids=("oxide",),
        )
        result = _solve(_recipe(_substrate(), _blanket("oxide", 0.5), blocker, etch))
        self.assertTrue(any(item.material_id == "oxide" for item in _stack(result, 5.0)))

    def test_isotropic_undercut_diagnostic(self) -> None:
        etch = ProcessStep(
            "iso",
            ProcessStepKind.ISOTROPIC_ETCH,
            etch_profile=EtchProfile(0.2, targets=("oxide",), lateral_attack=0.5),
        )
        result = _solve(_recipe(_substrate(), _patterned("oxide", (MaskInterval(2, 4),)), etch))
        self.assertIn("ISOTROPIC_UNDERCUT", _codes(result))

    def test_tapered_via_etch_diagnostic(self) -> None:
        etch = ProcessStep(
            "via",
            ProcessStepKind.TAPERED_ETCH,
            etch_profile=EtchProfile(0.3, targets=("oxide",), sidewall_angle_deg=82.0),
        )
        result = _solve(_recipe(_substrate(), _blanket("oxide", 0.7), etch))
        self.assertIn("TAPERED_PROFILE_APPROXIMATION", _codes(result))

    def test_cmp_overburden_removal(self) -> None:
        cmp = ProcessStep(
            "cmp",
            ProcessStepKind.CMP_PLANARIZATION,
            planarization_profile=PlanarizationProfile(1.1, ("metal",), overpolish=0.1),
        )
        result = _solve(_recipe(_substrate(), _blanket("metal", 0.5), cmp))
        top = max(interval.z_max for interval in result.frames[-1].profile.columns[0].intervals)
        self.assertLessEqual(top, 1.1)
        self.assertIn("CMP_HEURISTIC_USED", _codes(result))

    def test_cmp_dishing_heuristic_changes_height(self) -> None:
        plain = _solve(_recipe(_substrate(), _blanket("metal", 0.5), _cmp(0.0)))
        dished = _solve(_recipe(_substrate(), _blanket("metal", 0.5), _cmp(0.2)))
        self.assertLess(_top(dished, 5.0), _top(plain, 5.0))

    def test_process_window_variants_preserve_labels(self) -> None:
        recipe = _recipe(_substrate(), _blanket("oxide", 0.1))
        recipe = ProcessRecipe(recipe.id, recipe.name, recipe.materials, recipe.steps, (_window(),))
        labels = [
            item.variant_label
            for item in HybridCrossSectionSolver().solve_variants(SolverInput(recipe))
        ]
        self.assertEqual(labels, ["thickness:lower", "thickness:target", "thickness:upper"])

    def test_point_stack_and_cutline_extraction(self) -> None:
        options = SolverOptions(
            sample_count=21,
            point_sample_xs=(5.0,),
            cutline_x_min=4.0,
            cutline_x_max=6.0,
        )
        result = HybridCrossSectionSolver().solve(SolverInput(_recipe(_substrate()), options))
        self.assertEqual(len(result.point_samples), 1)
        self.assertGreater(len(result.cutline_samples), 1)

    def test_process_frame_sequence_and_pyxs_plan(self) -> None:
        recipe = _recipe(_substrate(), _blanket("oxide", 0.2), _cmp(0.0))
        result = _solve(recipe)
        plan = build_recipe_to_pyxs_plan(recipe)
        self.assertEqual([frame.step_id for frame in result.frames], ["substrate", "oxide", "cmp"])
        self.assertIn("cmp", plan.internal_only_step_ids)


def _banks() -> tuple[MaskInterval, ...]:
    return (MaskInterval(0, 3), MaskInterval(7, 10))


if __name__ == "__main__":
    unittest.main()
