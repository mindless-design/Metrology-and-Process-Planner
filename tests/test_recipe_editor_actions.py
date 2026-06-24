import unittest

from metrology_process_planner.app.command_types import CommandId
from metrology_process_planner.app.recipe_editor import RecipeEditorController
from metrology_process_planner.app.window_registry import WindowRegistry
from metrology_process_planner.domains.process import (
    Material,
    ProcessRecipe,
    ProcessStep,
    ProcessStepKind,
)
from metrology_process_planner.workflows import RecipeEditorActionDispatcher


class RecipeEditorActionTests(unittest.TestCase):
    def test_select_card_updates_in_memory_metadata_without_file_save(self) -> None:
        recipe = _recipe()

        result = RecipeEditorActionDispatcher().dispatch(recipe, "SelectRecipeCard:material:si")

        self.assertEqual("success", result.status)
        self.assertEqual("material:si", result.selected_card_id)
        self.assertEqual("material:si", result.recipe.metadata["selected_card_id"])
        self.assertNotIn("dirty", result.recipe.metadata)

    def test_add_process_step_template_marks_recipe_dirty_and_selects_step(self) -> None:
        recipe = _recipe()

        result = RecipeEditorActionDispatcher().dispatch(
            recipe,
            "AddProcessStep:directional_etch",
        )

        self.assertEqual("success", result.status)
        self.assertEqual(CommandId.ADD_PROCESS_STEP, result.command_id)
        self.assertEqual(2, len(result.recipe.steps))
        self.assertEqual(ProcessStepKind.DIRECTIONAL_ETCH, result.recipe.steps[-1].kind)
        self.assertTrue(result.recipe.metadata["dirty"])
        self.assertEqual(result.selected_card_id, result.recipe.metadata["selected_card_id"])

    def test_deferred_file_actions_return_structured_unavailable_result(self) -> None:
        result = RecipeEditorActionDispatcher().dispatch(_recipe(), "SaveRecipe")

        self.assertEqual("unavailable", result.status)
        self.assertEqual(CommandId.SAVE_RECIPE, result.command_id)
        self.assertIn("not wired", result.message)
        self.assertIn("modeless", result.next_ui_hint)

    def test_controller_dispatch_refreshes_modeless_recipe_window(self) -> None:
        registry: WindowRegistry[object] = WindowRegistry()
        controller = RecipeEditorController(window_registry=registry)
        controller.set_recipe(_recipe())

        opened = controller.open_current()
        result = controller.dispatch_action("AddProcessStep:blanket_deposition")

        self.assertEqual("success", result.status)
        self.assertIsNotNone(controller.last_action_result)
        self.assertEqual(2, len(controller.current_recipe.steps))
        self.assertEqual(1, opened.window["render_count"])
        view_model = opened.window["view_model"]
        self.assertEqual(2, len(view_model.step_cards))
        self.assertTrue(view_model.dirty)

    def test_validate_recipe_returns_clickable_warning_ids(self) -> None:
        recipe = ProcessRecipe("recipe-warning", "Warnings", (), ())

        result = RecipeEditorActionDispatcher().dispatch(recipe, "ValidateRecipe")

        self.assertEqual("warning", result.status)
        self.assertEqual(CommandId.VALIDATE_RECIPE, result.command_id)
        self.assertEqual(("recipe-warning-1", "recipe-warning-2"), result.warning_ids)


def _recipe() -> ProcessRecipe:
    return ProcessRecipe(
        "recipe-001",
        "Demo",
        (Material("si", "Silicon", "#aaa"),),
        (ProcessStep("substrate", ProcessStepKind.SUBSTRATE, "si"),),
    )


if __name__ == "__main__":
    unittest.main()
