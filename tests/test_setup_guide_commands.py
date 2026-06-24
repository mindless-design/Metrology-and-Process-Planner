import unittest
from dataclasses import replace

from metrology_process_planner.app.bootstrap import build_app_services
from metrology_process_planner.domains.session import SetupItemRecord, SetupState
from tests.editor_render_fixtures import session


class SetupGuideCommandTests(unittest.TestCase):
    def test_alignment_capture_action_arms_shared_box_capture(self) -> None:
        services = build_app_services()
        services.setup_guide_controller.set_active_session(session())
        opened = services.setup_guide_controller.open_current()

        result = opened.window["on_action"]("StartAlignmentCapture")
        refreshed = services.setup_guide_controller.open_current()
        active = services.setup_guide_controller.active_session

        self.assertEqual("success", result.status)
        self.assertIsNotNone(active)
        self.assertEqual("alignment_box_capture", active.workflow.stage)
        self.assertEqual("site_box", active.workflow.active_primitive)
        self.assertIn("Box capture armed", refreshed.view_model.capture_status_message)

    def test_origin_point_action_arms_shared_point_capture(self) -> None:
        services = build_app_services()
        services.setup_guide_controller.set_active_session(session())
        opened = services.setup_guide_controller.open_current()

        result = opened.window["on_action"]("StartOriginPointCapture")
        active = services.setup_guide_controller.active_session

        self.assertEqual("success", result.status)
        self.assertIsNotNone(active)
        self.assertEqual("origin_point_capture", active.workflow.stage)
        self.assertEqual("point", active.workflow.active_primitive)

    def test_coordinate_and_ready_actions_update_durable_setup_state(self) -> None:
        services = build_app_services()
        services.setup_guide_controller.set_active_session(session())
        opened = services.setup_guide_controller.open_current()

        origin = opened.window["on_action"]("UseOriginCoordinates")
        ready = opened.window["on_action"]("MarkSetupComplete")
        active = services.setup_guide_controller.active_session

        self.assertEqual("success", origin.status)
        self.assertEqual("success", ready.status)
        self.assertIsNotNone(active)
        self.assertEqual("origin", active.setup.coordinate_mode)
        self.assertTrue(active.setup.is_capture_ready)
        self.assertFalse(active.workflow.active)

    def test_skip_optional_setup_stage_marks_explicit_stage_skipped(self) -> None:
        services = build_app_services()
        source = replace(
            session(),
            setup=SetupState(
                items=(
                    SetupItemRecord(
                        "alignment",
                        "alignment_box_capture",
                        "Alignment",
                        "active",
                        metadata={"required": False},
                    ),
                )
            ),
        )
        services.setup_guide_controller.set_active_session(source)
        opened = services.setup_guide_controller.open_current()

        result = opened.window["on_action"]("SkipOptionalSetupStage")
        active = services.setup_guide_controller.active_session

        self.assertEqual("success", result.status)
        self.assertIsNotNone(active)
        self.assertEqual("skipped", active.setup.items[0].status)

    def test_validate_recipe_context_persists_setup_warning_state(self) -> None:
        services = build_app_services()
        services.setup_guide_controller.set_active_session(session())
        opened = services.setup_guide_controller.open_current()

        result = opened.window["on_action"]("ValidateRecipeContext")
        active = services.setup_guide_controller.active_session

        self.assertEqual("success", result.status)
        self.assertIsNotNone(active)
        self.assertIn("warn-process_recipe_missing", active.process_context.warning_ids)
        self.assertTrue(active.warnings)


if __name__ == "__main__":
    unittest.main()
