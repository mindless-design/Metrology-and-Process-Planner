import unittest
from dataclasses import replace

from metrology_process_planner.app.bootstrap import build_app_services
from metrology_process_planner.domains.session import (
    ModeDefinition,
    ModeRegistry,
    SessionMode,
    SessionModeId,
    SetupDefinition,
    SetupItemRecord,
)
from tests.editor_render_fixtures import session


def _skipped_item(item_id: str, item_type: str) -> SetupItemRecord:
    return SetupItemRecord(
        item_id,
        item_type,
        "Origin Point",
        "skipped",
        metadata={"required": False},
    )

def _external_setup_registry() -> ModeRegistry:
    return ModeRegistry(
        (
            ModeDefinition(
                "external_setup",
                "External Setup",
                setup=SetupDefinition(
                    required=True,
                    stage_types=(
                        "origin_choice",
                        "optional_origin_point",
                        "ready_for_capture",
                    ),
                ),
            ),
        )
    )

if __name__ == "__main__":
    unittest.main()


class SetupGuideRecipeValidationCommandTestsPart3(unittest.TestCase):
    def test_validate_recipe_context_persists_setup_warning_state(self) -> None:
        services = build_app_services()
        services.setup_guide_controller.set_active_session(
            replace(session(), mode=SessionMode.PROFILOMETRY_PLANNER)
        )
        opened = services.setup_guide_controller.open_current()

        result = opened.window["on_action"]("ValidateRecipeContext")
        active = services.setup_guide_controller.active_session

        self.assertEqual("success", result.status)
        self.assertIsNotNone(active)
        self.assertIn("warn-process_recipe_missing", active.process_context.warning_ids)
        self.assertTrue(active.warnings)

    def test_validate_recipe_context_is_blocked_for_non_process_setup(self) -> None:
        services = build_app_services()
        services.setup_guide_controller.set_active_session(session())
        opened = services.setup_guide_controller.open_current()

        result = opened.window["on_action"]("ValidateRecipeContext")
        active = services.setup_guide_controller.active_session

        self.assertEqual("blocked", result.status)
        self.assertIn("recipe-free mode", result.message)
        self.assertIsNotNone(active)
        self.assertEqual((), active.process_context.warning_ids)

    def test_external_recipe_free_setup_uses_injected_mode_registry(self) -> None:
        registry = _external_setup_registry()
        services = build_app_services(mode_registry=registry)
        source = replace(session(), mode=SessionModeId("external_setup"))
        services.setup_guide_controller.set_active_session(source)
        opened = services.setup_guide_controller.open_current()

        self.assertEqual("External Setup", opened.view_model.mode_display_name)
        self.assertEqual(
            ("origin_choice", "optional_origin_point", "ready_for_capture"),
            tuple(stage.stage_id for stage in opened.view_model.stages),
        )
        self.assertEqual(
            ("origin_choice", "origin_point_capture", "ready_for_capture"),
            tuple(stage.stage_type for stage in opened.view_model.stages),
        )

        opened.window["on_action"]("UseGlobalCoordinates")
        skipped = opened.window["on_action"]("SkipOptionalSetupStage")
        recipe = opened.window["on_action"]("ValidateRecipeContext")
        active = services.setup_guide_controller.active_session

        self.assertEqual("success", skipped.status)
        self.assertEqual("blocked", recipe.status)
        self.assertIn("recipe-free mode", recipe.message)
        self.assertIsNotNone(active)
        self.assertEqual(("optional_origin_point",), tuple(item.id for item in active.setup.items))
        self.assertEqual(("skipped",), tuple(item.status for item in active.setup.items))
        self.assertEqual((), active.process_context.warning_ids)
