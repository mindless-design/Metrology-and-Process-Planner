import tempfile
import unittest
from pathlib import Path

from metrology_process_planner.app.bootstrap import build_app_services
from metrology_process_planner.app.commands import CommandId
from metrology_process_planner.app.recipe_path_adapter import RecipePathSelection
from metrology_process_planner.domains.process import (
    Material,
    ProcessRecipe,
    ProcessStep,
    ProcessStepKind,
)
from metrology_process_planner.persistence.recipe_store import ProcessRecipeJsonStore
from tests.process_context_fixtures import session as process_session


class RecipePathAdapterCommandTests(unittest.TestCase):
    def test_open_recipe_command_uses_adapter_selected_path(self) -> None:
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder) / "recipe.json"
            ProcessRecipeJsonStore().save(_recipe(), path)
            services = build_app_services(recipe_path_adapter=_Adapter(open_path=path))

            result = services.command_router.route(CommandId.OPEN_RECIPE)

            self.assertEqual("success", result.status)
            self.assertEqual(CommandId.OPEN_RECIPE, result.command_id)
            self.assertEqual(str(path), result.output_path)
            recipe_path = services.recipe_editor_controller.current_recipe.metadata["recipe_path"]
            self.assertEqual(path, Path(recipe_path))

    def test_open_recipe_cancel_is_non_mutating(self) -> None:
        services = build_app_services(recipe_path_adapter=_Adapter())

        result = services.command_router.route(CommandId.OPEN_RECIPE)

        self.assertEqual("cancelled", result.status)
        self.assertIsNone(services.recipe_editor_controller.current_recipe)

    def test_save_recipe_as_command_uses_adapter_destination(self) -> None:
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder) / "saved-recipe.json"
            services = build_app_services(recipe_path_adapter=_Adapter(save_path=path))
            services.recipe_editor_controller.set_recipe(_recipe(dirty=True))

            result = services.command_router.route(CommandId.SAVE_RECIPE_AS)

            self.assertEqual("success", result.status)
            self.assertEqual(CommandId.SAVE_RECIPE_AS, result.command_id)
            self.assertEqual(str(path), result.output_path)
            self.assertTrue(path.exists())
            self.assertNotIn("dirty", services.recipe_editor_controller.current_recipe.metadata)

    def test_setup_attach_recipe_command_uses_adapter_selected_path(self) -> None:
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder) / "recipe.json"
            ProcessRecipeJsonStore().save(_recipe(), path)
            services = build_app_services(recipe_path_adapter=_Adapter(attach_path=path))
            services.setup_guide_controller.set_active_session(process_session())

            result = services.command_router.route(CommandId.ATTACH_RECIPE)

            self.assertEqual("success", result.status)
            self.assertEqual(CommandId.ATTACH_RECIPE, result.command_id)
            context = services.setup_guide_controller.active_session.process_context
            self.assertEqual(str(path), context.recipe_path)


class _Adapter:
    def __init__(
        self,
        open_path: Path | None = None,
        save_path: Path | None = None,
        attach_path: Path | None = None,
    ) -> None:
        self._open_path = open_path
        self._save_path = save_path
        self._attach_path = attach_path

    def select_open_recipe(self) -> RecipePathSelection:
        if self._open_path is None:
            return RecipePathSelection(status="cancelled", message="Open Recipe cancelled.")
        return RecipePathSelection.selected(self._open_path)

    def select_save_recipe_as(self) -> RecipePathSelection:
        if self._save_path is None:
            return RecipePathSelection(status="cancelled", message="Save Recipe As cancelled.")
        return RecipePathSelection.selected(self._save_path)

    def select_attach_recipe(self) -> RecipePathSelection:
        if self._attach_path is None:
            return RecipePathSelection(status="cancelled", message="Attach Recipe cancelled.")
        return RecipePathSelection.selected(self._attach_path)


def _recipe(dirty: bool = False) -> ProcessRecipe:
    metadata = {"dirty": True} if dirty else {}
    return ProcessRecipe(
        "recipe-001",
        "Demo",
        (Material("si", "Silicon", "#aaa"),),
        (ProcessStep("substrate", ProcessStepKind.SUBSTRATE, "si"),),
        metadata=metadata,
    )


if __name__ == "__main__":
    unittest.main()
