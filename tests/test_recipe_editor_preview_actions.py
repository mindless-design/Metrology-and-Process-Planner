import unittest

from metrology_process_planner.app.command_types import CommandId
from metrology_process_planner.domains.process import (
    Material,
    ProcessRecipe,
    ProcessStep,
    ProcessStepKind,
)
from metrology_process_planner.ui.recipe_editor import RecipeEditorPresenter
from metrology_process_planner.workflows import RecipeEditorActionDispatcher


class RecipeEditorPreviewActionTests(unittest.TestCase):
    def test_preview_full_recipe_records_scope_without_dirtying_recipe(self) -> None:
        result = RecipeEditorActionDispatcher().dispatch(_recipe(), "PreviewRecipe")

        self.assertEqual("warning", result.status)
        self.assertEqual(CommandId.PREVIEW_RECIPE, result.command_id)
        self.assertEqual("full_recipe", result.recipe.metadata["preview_scope"])
        self.assertEqual("", result.recipe.metadata["selected_step_id"])
        self.assertNotIn("dirty", result.recipe.metadata)
        self.assertEqual(("recipe-preview-backend-unavailable",), result.warning_ids)

    def test_preview_through_step_selects_step_and_updates_preview_model(self) -> None:
        result = RecipeEditorActionDispatcher().dispatch(
            _recipe(),
            "PreviewRecipeThroughStep:deposit",
        )
        view_model = RecipeEditorPresenter().build(result.recipe)

        self.assertEqual("warning", result.status)
        self.assertEqual(CommandId.PREVIEW_RECIPE_THROUGH_STEP, result.command_id)
        self.assertEqual("through_step", result.recipe.metadata["preview_scope"])
        self.assertEqual("step:deposit", result.recipe.metadata["selected_card_id"])
        self.assertEqual("deposit", view_model.preview.selected_step_id)

    def test_preview_through_missing_step_returns_modeless_error(self) -> None:
        result = RecipeEditorActionDispatcher().dispatch(
            _recipe(),
            "PreviewRecipeThroughStep:missing",
        )

        self.assertEqual("error", result.status)
        self.assertEqual(CommandId.PREVIEW_RECIPE_THROUGH_STEP, result.command_id)
        self.assertIn("not found", result.message)


def _recipe() -> ProcessRecipe:
    return ProcessRecipe(
        "recipe-preview",
        "Preview Demo",
        (Material("si", "Silicon", "#aaa"), Material("oxide", "Oxide", "#88ccff")),
        (
            ProcessStep("substrate", ProcessStepKind.SUBSTRATE, "si"),
            ProcessStep("deposit", ProcessStepKind.BLANKET_DEPOSITION, "oxide"),
        ),
    )


if __name__ == "__main__":
    unittest.main()
