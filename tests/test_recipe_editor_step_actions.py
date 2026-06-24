import unittest

from metrology_process_planner.app.command_types import CommandId
from metrology_process_planner.domains.process import (
    MaskPolarity,
    Material,
    ProcessRecipe,
    ProcessStep,
    ProcessStepKind,
)
from metrology_process_planner.workflows import RecipeEditorActionDispatcher


class RecipeEditorStepActionTests(unittest.TestCase):
    def test_duplicate_step_inserts_copy_and_selects_it(self) -> None:
        result = RecipeEditorActionDispatcher().dispatch(
            _two_step_recipe(),
            "DuplicateProcessStep:deposit",
        )

        self.assertEqual("success", result.status)
        self.assertEqual(CommandId.DUPLICATE_PROCESS_STEP, result.command_id)
        self.assertEqual(("substrate", "deposit", "deposit-copy"), _step_ids(result.recipe))
        self.assertEqual("step:deposit-copy", result.selected_card_id)
        self.assertTrue(result.recipe.metadata["dirty"])

    def test_move_and_disable_step_update_order_and_enabled_state(self) -> None:
        moved = RecipeEditorActionDispatcher().dispatch(
            _two_step_recipe(),
            "MoveProcessStepUp:deposit",
        )
        disabled = RecipeEditorActionDispatcher().dispatch(
            moved.recipe,
            "DisableProcessStep:deposit",
        )

        self.assertEqual(("deposit", "substrate"), _step_ids(moved.recipe))
        self.assertEqual("success", disabled.status)
        self.assertFalse(disabled.recipe.steps[0].parameters["enabled"])
        self.assertEqual("step:deposit", disabled.selected_card_id)

    def test_move_first_step_up_returns_inline_blocked_result(self) -> None:
        result = RecipeEditorActionDispatcher().dispatch(
            _two_step_recipe(),
            "MoveProcessStepUp:substrate",
        )

        self.assertEqual("blocked", result.status)
        self.assertEqual(CommandId.MOVE_PROCESS_STEP_UP, result.command_id)
        self.assertIn("cannot move", result.message)
        self.assertEqual("step:substrate", result.selected_card_id)

    def test_edit_step_updates_name_material_and_thickness(self) -> None:
        named = RecipeEditorActionDispatcher().dispatch(
            _two_step_recipe(),
            "EditProcessStep:deposit:name:ILD Oxide",
        )
        material = RecipeEditorActionDispatcher().dispatch(
            named.recipe,
            "EditProcessStep:deposit:material_id:si",
        )
        thick = RecipeEditorActionDispatcher().dispatch(
            material.recipe,
            "EditProcessStep:deposit:thickness:0.125",
        )

        step = thick.recipe.steps[1]
        self.assertEqual("success", thick.status)
        self.assertEqual(CommandId.EDIT_PROCESS_STEP, thick.command_id)
        self.assertEqual("ILD Oxide", step.parameters["name"])
        self.assertEqual("si", step.material_id)
        self.assertEqual(0.125, step.thickness.target)
        self.assertTrue(thick.recipe.metadata["dirty"])
        self.assertEqual("step:deposit", thick.selected_card_id)

    def test_edit_step_updates_targets_stops_and_mask_polarity(self) -> None:
        targets = RecipeEditorActionDispatcher().dispatch(
            _two_step_recipe(),
            "EditProcessStep:deposit:target_material_ids:oxide, si",
        )
        stops = RecipeEditorActionDispatcher().dispatch(
            targets.recipe,
            "EditProcessStep:deposit:stop_material_ids:metal",
        )
        polarity = RecipeEditorActionDispatcher().dispatch(
            stops.recipe,
            "EditProcessStep:deposit:mask_polarity:inverted",
        )

        step = polarity.recipe.steps[1]
        self.assertEqual(("oxide", "si"), step.target_material_ids)
        self.assertEqual(("metal",), step.stop_material_ids)
        self.assertEqual(MaskPolarity.INVERTED, step.mask_polarity)

    def test_edit_step_rejects_bad_payload_modelessly(self) -> None:
        result = RecipeEditorActionDispatcher().dispatch(
            _two_step_recipe(),
            "EditProcessStep:deposit:thickness:not-a-number",
        )

        self.assertEqual("error", result.status)
        self.assertEqual(CommandId.EDIT_PROCESS_STEP, result.command_id)
        self.assertIn("numeric", result.message)


def _two_step_recipe() -> ProcessRecipe:
    return ProcessRecipe(
        "recipe-002",
        "Two Step",
        (Material("si", "Silicon", "#aaa"), Material("oxide", "Oxide", "#88ccff")),
        (
            ProcessStep("substrate", ProcessStepKind.SUBSTRATE, "si"),
            ProcessStep(
                "deposit",
                ProcessStepKind.BLANKET_DEPOSITION,
                "oxide",
                parameters={"enabled": True},
            ),
        ),
    )


def _step_ids(recipe: ProcessRecipe) -> tuple[str, ...]:
    return tuple(step.id for step in recipe.steps)


if __name__ == "__main__":
    unittest.main()
