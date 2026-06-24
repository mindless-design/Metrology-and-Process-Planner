import tempfile
import unittest
from pathlib import Path

from metrology_process_planner.app.command_types import CommandId
from metrology_process_planner.app.recipe_editor import RecipeEditorController
from metrology_process_planner.app.window_registry import WindowRegistry
from metrology_process_planner.domains.process import (
    Material,
    ProcessRecipe,
    ProcessStep,
    ProcessStepKind,
)
from metrology_process_planner.persistence.recipe_store import ProcessRecipeJsonStore


class RecipeEditorOpeningTests(unittest.TestCase):
    def test_new_recipe_creates_dirty_starter_recipe(self) -> None:
        controller = RecipeEditorController()

        result = controller.dispatch_action("NewRecipe")

        self.assertEqual("success", result.status)
        self.assertEqual(CommandId.NEW_RECIPE, result.command_id)
        self.assertEqual("untitled-recipe", controller.current_recipe.id)
        self.assertTrue(controller.current_recipe.metadata["dirty"])
        self.assertEqual("material:si", result.selected_card_id)

    def test_dirty_new_recipe_is_blocked_until_discard_confirmed(self) -> None:
        controller = RecipeEditorController()
        controller.set_recipe(_recipe(metadata={"dirty": True}))

        blocked = controller.dispatch_action("NewRecipe")
        confirmed = controller.dispatch_action("NewRecipe:discard")

        self.assertEqual("blocked", blocked.status)
        self.assertEqual("success", confirmed.status)
        self.assertEqual("untitled-recipe", controller.current_recipe.id)

    def test_open_recipe_loads_path_and_refreshes_single_window(self) -> None:
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder) / "recipe.json"
            ProcessRecipeJsonStore().save(_recipe("opened"), path)
            registry: WindowRegistry[object] = WindowRegistry()
            controller = RecipeEditorController(window_registry=registry)
            controller.set_recipe(_recipe("old"))
            controller.open_current()

            result = controller.dispatch_action(f"OpenRecipe:{path}")

            self.assertEqual("success", result.status)
            self.assertEqual(CommandId.OPEN_RECIPE, result.command_id)
            self.assertEqual("opened", controller.current_recipe.id)
            self.assertEqual(str(path), controller.current_recipe.metadata["recipe_path"])
            self.assertFalse(registry.is_open("recipe-editor:old"))

    def test_dirty_open_recipe_is_blocked_until_discard_confirmed(self) -> None:
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder) / "recipe.json"
            ProcessRecipeJsonStore().save(_recipe("opened"), path)
            controller = RecipeEditorController()
            controller.set_recipe(_recipe("old", metadata={"dirty": True}))

            blocked = controller.dispatch_action(f"OpenRecipe:{path}")
            confirmed = controller.dispatch_action(f"OpenRecipe:discard:{path}")

            self.assertEqual("blocked", blocked.status)
            self.assertEqual("success", confirmed.status)
            self.assertEqual("opened", controller.current_recipe.id)

    def test_open_recipe_without_path_or_bad_file_returns_modeless_result(self) -> None:
        controller = RecipeEditorController()

        missing_path = controller.dispatch_action("OpenRecipe")
        bad_file = controller.dispatch_action("OpenRecipe:does-not-exist.json")

        self.assertEqual("unavailable", missing_path.status)
        self.assertEqual("error", bad_file.status)
        self.assertEqual(CommandId.OPEN_RECIPE, bad_file.command_id)


def _recipe(
    recipe_id: str = "recipe-001",
    metadata: dict[str, object] | None = None,
) -> ProcessRecipe:
    return ProcessRecipe(
        recipe_id,
        "Demo",
        (Material("si", "Silicon", "#aaa"),),
        (ProcessStep("substrate", ProcessStepKind.SUBSTRATE, "si"),),
        metadata=metadata,
    )


if __name__ == "__main__":
    unittest.main()
