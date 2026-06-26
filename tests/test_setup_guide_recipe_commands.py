import tempfile
import unittest
from dataclasses import replace
from pathlib import Path

from metrology_process_planner.app.bootstrap import build_app_services
from metrology_process_planner.app.commands import CommandId
from metrology_process_planner.app.recipe_path_adapter import RecipePathSelection
from metrology_process_planner.domains.session import ModeDefinition, ModeRegistry, SessionModeId
from metrology_process_planner.workflows.editor import SessionDocumentBuilder
from tests.process_context_fixtures import recipe_path, session
from tests.recipe_path_fixtures import FakeRecipePathAdapter


class SetupGuideRecipeCommandTests(unittest.TestCase):
    def test_attach_recipe_action_uses_injected_path_picker(self) -> None:
        with tempfile.TemporaryDirectory() as folder:
            path = recipe_path(Path(folder))
            services = build_app_services(
                recipe_path_adapter=FakeRecipePathAdapter(
                    attach_recipe=RecipePathSelection.selected(path)
                )
            )
            document = SessionDocumentBuilder().build(session())
            services.session_editor_controller.open_document(document)
            services.command_router.route(CommandId.OPEN_SETUP_GUIDE)
            opened = services.setup_guide_controller.open_current()

            result = opened.window["on_action"]("AttachRecipe")
            active = services.session_editor_controller.current_document.session

            self.assertEqual("success", result.status)
            self.assertEqual("recipe_gate_stack", active.process_context.recipe_id)
            self.assertEqual(str(path), active.process_context.recipe_path)

    def test_external_recipe_free_setup_attach_recipe_uses_loaded_registry_guard(self) -> None:
        registry = ModeRegistry((ModeDefinition("external_mode", "External Mode"),))
        with tempfile.TemporaryDirectory() as folder:
            path = recipe_path(Path(folder))
            services = build_app_services(
                mode_registry=registry,
                recipe_path_adapter=FakeRecipePathAdapter(
                    attach_recipe=RecipePathSelection.selected(path)
                ),
            )
            source = replace(session(), mode=SessionModeId("external_mode"))
            services.setup_guide_controller.set_active_session(source)

            result = services.command_router.route(CommandId.ATTACH_RECIPE)

            active = services.setup_guide_controller.active_session
            self.assertEqual("blocked", result.status)
            self.assertIn("recipe-free mode", result.message)
            self.assertIsNotNone(active)
            assert active is not None
            self.assertEqual("", active.process_context.recipe_id)
            self.assertEqual("", active.process_context.recipe_path)


if __name__ == "__main__":
    unittest.main()
