import unittest

from metrology_process_planner.app.bootstrap import build_app_services
from metrology_process_planner.app.recipe_editor import RecipeEditorController
from metrology_process_planner.app.setup_guide import SetupGuideController
from metrology_process_planner.app.window_registry import WindowRegistry
from metrology_process_planner.domains.process import Material, ProcessRecipe
from tests.editor_render_fixtures import session


class ModelessSurfaceRegistryTests(unittest.TestCase):
    def test_setup_guide_uses_shared_registry_and_reuses_window(self) -> None:
        registry: WindowRegistry[object] = WindowRegistry()
        controller = SetupGuideController(window_registry=registry)
        controller.set_active_session(session())

        first = controller.open_current()
        second = controller.open_current()

        self.assertEqual("opened", first.status)
        self.assertEqual("raised", second.status)
        self.assertIs(first.window, second.window)
        self.assertTrue(second.window["resizable"])
        self.assertTrue(second.window["fits_1366x768"])
        self.assertTrue(registry.is_open("setup-guide:session-001"))

    def test_recipe_editor_uses_shared_registry_and_reuses_window(self) -> None:
        registry: WindowRegistry[object] = WindowRegistry()
        controller = RecipeEditorController(window_registry=registry)
        controller.set_recipe(
            ProcessRecipe(
                "recipe-001",
                "Demo Recipe",
                (Material("si", "Si", "#aaa"),),
                (),
            )
        )

        first = controller.open_current()
        second = controller.open_current()

        self.assertEqual("opened", first.status)
        self.assertEqual("raised", second.status)
        self.assertIs(first.window, second.window)
        self.assertTrue(second.window["scrollable"])
        self.assertTrue(registry.is_open("recipe-editor:recipe-001"))

    def test_diagnostics_reports_open_modeless_windows(self) -> None:
        services = build_app_services()
        services.setup_guide_controller.set_active_session(session())
        services.setup_guide_controller.open_current()
        services.recipe_editor_controller.open_current()
        services.diagnostics_controller.set_active_session(session())

        result = services.diagnostics_controller.open_current()
        summary = dict(result.window["summary"])

        self.assertIn("Setup Guide - Demo", summary["Open Windows"])
        self.assertIn("Recipe Editor - No recipe loaded", summary["Open Windows"])
        self.assertIn("Advanced Diagnostics", summary["Open Windows"])

    def test_setup_guide_actions_route_through_command_router(self) -> None:
        services = build_app_services()
        services.setup_guide_controller.set_active_session(session())
        opened = services.setup_guide_controller.open_current()

        unavailable = opened.window["on_action"]("StartOriginPointCapture")
        closed = opened.window["on_action"]("CloseSetupGuide")

        self.assertEqual("unavailable", unavailable.status)
        self.assertIn("not wired", unavailable.next_ui_hint)
        self.assertEqual("success", closed.status)
        self.assertFalse(services.window_registry.is_open("setup-guide:session-001"))
        self.assertEqual(closed, services.setup_guide_controller.last_action_result)


if __name__ == "__main__":
    unittest.main()
