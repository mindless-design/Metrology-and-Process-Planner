import unittest

from metrology_process_planner.domains.process import (
    Material,
    ProcessRecipe,
    ProcessStep,
    ProcessStepKind,
)
from metrology_process_planner.ui.recipe_editor import RecipeEditorPresenter
from metrology_process_planner.workflows import RecipeEditorActionDispatcher


class RecipeEditorStepCardTests(unittest.TestCase):
    def test_enabled_step_card_exposes_status_and_actions(self) -> None:
        card = RecipeEditorPresenter().build(_recipe(enabled=True)).step_cards[0]

        self.assertEqual("Enabled", card.status_label)
        self.assertEqual(
            (
                "DuplicateProcessStep:deposit",
                "DeleteProcessStep:deposit",
                "MoveProcessStepUp:deposit",
                "MoveProcessStepDown:deposit",
                "DisableProcessStep:deposit",
                "PreviewRecipeThroughStep:deposit",
            ),
            tuple(action.action_id for action in card.actions),
        )

    def test_disabled_step_card_exposes_enable_action(self) -> None:
        view_model = RecipeEditorPresenter().build(_recipe(enabled=False))
        card = view_model.step_cards[0]
        detail = view_model.selected_detail

        self.assertEqual("Disabled", card.status_label)
        self.assertIn("EnableProcessStep:deposit", [action.action_id for action in card.actions])
        self.assertIsNotNone(detail)
        assert detail is not None
        self.assertIn("Enable Step", [action.label for action in detail.actions])
        self.assertNotIn("Disable Step", [action.label for action in detail.actions])

    def test_step_card_preview_action_updates_modeless_preview_state(self) -> None:
        action_id = RecipeEditorPresenter().build(_recipe(enabled=True)).step_cards[0].actions[-1]

        result = RecipeEditorActionDispatcher().dispatch(_recipe(enabled=True), action_id.action_id)

        self.assertEqual("warning", result.status)
        self.assertEqual("through_step", result.recipe.metadata["preview_scope"])
        self.assertEqual("step:deposit", result.recipe.metadata["selected_card_id"])


def _recipe(enabled: bool) -> ProcessRecipe:
    return ProcessRecipe(
        "recipe-step-cards",
        "Step Cards",
        (Material("oxide", "Oxide", "#88ccff"),),
        (
            ProcessStep(
                "deposit",
                ProcessStepKind.BLANKET_DEPOSITION,
                "oxide",
                parameters={"enabled": enabled},
            ),
        ),
        metadata={"selected_card_id": "step:deposit"},
    )


if __name__ == "__main__":
    unittest.main()
