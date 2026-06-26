import json
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
from metrology_process_planner.persistence.recipe_store import JsonPath, ProcessRecipeJsonStore
from tests.process_context_fixtures import session


class _FailingRecipeStore(ProcessRecipeJsonStore):
    def save(self, recipe: ProcessRecipe, path: JsonPath) -> Path:
        raise OSError("disk full")

def _recipe(path: Path | None, name: str = "Demo", dirty: bool = False) -> ProcessRecipe:
    metadata: dict[str, object] = {}
    if path is not None:
        metadata["recipe_path"] = str(path)
    if dirty:
        metadata["dirty"] = True
    return ProcessRecipe(
        "recipe-001",
        name,
        (Material("si", "Silicon", "#aaa"),),
        (ProcessStep("substrate", ProcessStepKind.SUBSTRATE, "si"),),
        metadata=metadata,
    )

if __name__ == "__main__":
    unittest.main()


class RecipeEditorSaveTestsPart1(unittest.TestCase):
    def test_recipe_store_writes_human_readable_json_and_backup(self) -> None:
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder) / "recipe.json"
            store = ProcessRecipeJsonStore()

            store.save(_recipe(path), path)
            store.save(_recipe(path, name="Updated"), path)

            payload = json.loads(path.read_text(encoding="utf-8"))
            self.assertEqual("Updated", payload["name"])
            self.assertTrue(path.with_suffix(".json.bak").exists())

    def test_controller_save_clears_dirty_state_and_refreshes_window(self) -> None:
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder) / "recipe.json"
            registry: WindowRegistry[object] = WindowRegistry()
            controller = RecipeEditorController(window_registry=registry)
            controller.set_recipe(_recipe(path, dirty=True))
            opened = controller.open_current()

            result = opened.window["on_action"]("SaveRecipe")

            self.assertEqual("success", result.status)
            self.assertEqual(CommandId.SAVE_RECIPE, result.command_id)
            self.assertNotIn("dirty", controller.current_recipe.metadata)
            self.assertEqual(1, opened.window["render_count"])
            self.assertTrue(path.exists())

    def test_controller_save_without_path_returns_modeless_unavailable(self) -> None:
        controller = RecipeEditorController()
        controller.set_recipe(_recipe(None, dirty=True))

        result = controller.dispatch_action("SaveRecipe")

        self.assertEqual("unavailable", result.status)
        self.assertEqual(CommandId.SAVE_RECIPE, result.command_id)
        self.assertTrue(result.recipe.metadata["dirty"])

    def test_controller_save_as_sets_path_and_clears_dirty_state(self) -> None:
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder) / "saved-as.json"
            controller = RecipeEditorController()
            controller.set_recipe(_recipe(None, dirty=True))

            result = controller.dispatch_action(f"SaveRecipeAs:{path}")

            self.assertEqual("success", result.status)
            self.assertEqual(CommandId.SAVE_RECIPE_AS, result.command_id)
            self.assertEqual(str(path), controller.current_recipe.metadata["recipe_path"])
            self.assertNotIn("dirty", controller.current_recipe.metadata)
            self.assertTrue(path.exists())

    def test_controller_save_as_without_path_returns_unavailable(self) -> None:
        controller = RecipeEditorController()
        controller.set_recipe(_recipe(None, dirty=True))

        result = controller.dispatch_action("SaveRecipeAs")

        self.assertEqual("unavailable", result.status)
        self.assertEqual(CommandId.SAVE_RECIPE_AS, result.command_id)
        self.assertTrue(result.recipe.metadata["dirty"])

    def test_controller_save_failure_preserves_dirty_recipe(self) -> None:
        controller = RecipeEditorController(recipe_store=_FailingRecipeStore())
        controller.set_recipe(_recipe(Path("blocked.json"), dirty=True))

        result = controller.dispatch_action("SaveRecipe")

        self.assertEqual("error", result.status)
        self.assertEqual(CommandId.SAVE_RECIPE, result.command_id)
        self.assertTrue(controller.current_recipe.metadata["dirty"])

    def test_attach_recipe_to_active_session_updates_process_context(self) -> None:
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder) / "recipe.json"
            ProcessRecipeJsonStore().save(_recipe(path), path)
            active = {"session": session()}
            controller = RecipeEditorController(
                active_session_provider=lambda: active["session"],
                active_session_updater=lambda updated: active.update(session=updated),
            )
            controller.set_recipe(_recipe(path))

            result = controller.dispatch_action("AttachRecipeToActiveSession")

            self.assertEqual("success", result.status)
            self.assertEqual(CommandId.ATTACH_RECIPE_TO_ACTIVE_SESSION, result.command_id)
            self.assertEqual("recipe-001", active["session"].process_context.recipe_id)
            self.assertEqual(str(path), active["session"].process_context.recipe_path)
