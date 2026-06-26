import tempfile
import unittest
from dataclasses import replace
from pathlib import Path

from metrology_process_planner.app.command_types import CommandId
from metrology_process_planner.app.recipe_editor import RecipeEditorController
from metrology_process_planner.domains.process import (
    Material,
    ProcessRecipe,
    ProcessStep,
    ProcessStepKind,
)
from metrology_process_planner.domains.session import ModeDefinition, ModeRegistry, SessionModeId
from metrology_process_planner.persistence.recipe_store import JsonPath, ProcessRecipeJsonStore
from tests.editor_render_fixtures import session as simple_session


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


class RecipeEditorSaveTestsPart2(unittest.TestCase):
    def test_attach_recipe_blocks_dirty_or_missing_session_modelessly(self) -> None:
        controller = RecipeEditorController()
        controller.set_recipe(_recipe(Path("recipe.json"), dirty=True))

        dirty = controller.dispatch_action("AttachRecipeToActiveSession")

        self.assertEqual("blocked", dirty.status)
        self.assertEqual(CommandId.ATTACH_RECIPE_TO_ACTIVE_SESSION, dirty.command_id)

        clean = RecipeEditorController(
            active_session_provider=lambda: None,
            active_session_updater=lambda updated: None,
        )
        clean.set_recipe(_recipe(Path("recipe.json")))

        missing = clean.dispatch_action("AttachRecipeToActiveSession")

        self.assertEqual("unavailable", missing.status)
        self.assertEqual("No active session is loaded.", missing.message)

    def test_attach_recipe_to_active_session_rejects_recipe_free_mode(self) -> None:
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder) / "recipe.json"
            ProcessRecipeJsonStore().save(_recipe(path), path)
            active = {"session": simple_session()}
            controller = RecipeEditorController(
                active_session_provider=lambda: active["session"],
                active_session_updater=lambda updated: active.update(session=updated),
            )
            controller.set_recipe(_recipe(path))

            result = controller.dispatch_action("AttachRecipeToActiveSession")

            self.assertEqual("unavailable", result.status)
            self.assertEqual(CommandId.ATTACH_RECIPE_TO_ACTIVE_SESSION, result.command_id)
            self.assertIn("recipe-free mode", result.message)
            self.assertEqual("", active["session"].process_context.recipe_id)

    def test_external_recipe_free_mode_rejects_recipe_attachment_with_loaded_registry(self) -> None:
        registry = ModeRegistry((ModeDefinition("external_mode", "External Mode"),))
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder) / "recipe.json"
            ProcessRecipeJsonStore().save(_recipe(path), path)
            active = {"session": replace(simple_session(), mode=SessionModeId("external_mode"))}
            controller = RecipeEditorController(
                active_session_provider=lambda: active["session"],
                active_session_updater=lambda updated: active.update(session=updated),
                mode_registry=registry,
            )
            controller.set_recipe(_recipe(path))

            result = controller.dispatch_action("AttachRecipeToActiveSession")

            self.assertEqual("unavailable", result.status)
            self.assertEqual(CommandId.ATTACH_RECIPE_TO_ACTIVE_SESSION, result.command_id)
            self.assertIn("recipe-free mode", result.message)
            self.assertEqual("", active["session"].process_context.recipe_id)
