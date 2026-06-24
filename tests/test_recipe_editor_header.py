import unittest

from metrology_process_planner.domains.process import (
    Material,
    ProcessRecipe,
    ProcessStep,
    ProcessStepKind,
)
from metrology_process_planner.ui.recipe_editor import RecipeEditorPresenter


class RecipeEditorHeaderTests(unittest.TestCase):
    def test_header_surfaces_path_dirty_validation_and_attach_state(self) -> None:
        view_model = RecipeEditorPresenter().build(_dirty_saved_recipe())
        actions = {action.action_id: action for action in view_model.header_actions}

        self.assertEqual("recipes/saved.json", view_model.header.recipe_path)
        self.assertTrue(view_model.header.dirty)
        self.assertEqual("valid", view_model.header.validation_status)
        self.assertEqual("dirty", view_model.header.attachment_status)
        self.assertFalse(actions["AttachRecipeToActiveSession"].enabled)
        self.assertEqual(
            "Save the recipe before attaching it.",
            actions["AttachRecipeToActiveSession"].disabled_reason,
        )

    def test_empty_header_disables_recipe_specific_actions(self) -> None:
        view_model = RecipeEditorPresenter().build(None)
        actions = {action.action_id: action for action in view_model.header_actions}

        self.assertEqual("unloaded", view_model.header.validation_status)
        self.assertFalse(actions["SaveRecipe"].enabled)
        self.assertFalse(actions["ValidateRecipe"].enabled)
        self.assertFalse(actions["PreviewRecipe"].enabled)
        self.assertEqual(
            "Load or create a recipe first.",
            actions["ValidateRecipe"].disabled_reason,
        )

    def test_unsaved_recipe_header_guides_save_as_before_save(self) -> None:
        view_model = RecipeEditorPresenter().build(_recipe(metadata={}))
        actions = {action.action_id: action for action in view_model.header_actions}

        self.assertEqual("unsaved", view_model.header.attachment_status)
        self.assertFalse(actions["SaveRecipe"].enabled)
        self.assertEqual(
            "Use Save As before Save for a new recipe.",
            actions["SaveRecipe"].disabled_reason,
        )


def _dirty_saved_recipe() -> ProcessRecipe:
    return _recipe(metadata={"dirty": True, "recipe_path": "recipes/saved.json"})


def _recipe(metadata: dict[str, object] | None = None) -> ProcessRecipe:
    return ProcessRecipe(
        "recipe-saved",
        "Saved Dirty Recipe",
        (Material("si", "Silicon", "#aaa"),),
        (ProcessStep("substrate", ProcessStepKind.SUBSTRATE, "si"),),
        metadata=metadata,
    )


if __name__ == "__main__":
    unittest.main()
