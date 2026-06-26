import unittest
from dataclasses import replace

from metrology_process_planner.app.bootstrap import build_app_services
from metrology_process_planner.app.commands import CommandId
from metrology_process_planner.domains.session import (
    ModeDefinition,
    ModeRegistry,
    SessionMode,
    SetupDefinition,
    SetupItemRecord,
    SetupState,
)
from metrology_process_planner.workflows.editor import SessionDocumentBuilder
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


class SetupGuideCommandTestsPart1(unittest.TestCase):
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

    def test_setup_action_updates_active_editor_document(self) -> None:
        services = build_app_services()
        document = SessionDocumentBuilder().build(
            replace(session(), mode=SessionMode.OPTICAL_METROLOGY)
        )
        services.session_editor_controller.open_document(document)
        services.command_router.route(CommandId.OPEN_SETUP_GUIDE)
        opened = services.setup_guide_controller.open_current()

        result = opened.window["on_action"]("UseOriginCoordinates")
        editor_document = services.session_editor_controller.current_document

        self.assertEqual("success", result.status)
        self.assertIsNotNone(editor_document)
        self.assertEqual("origin", editor_document.session.setup.coordinate_mode)

    def test_setup_action_refreshes_open_modeless_window(self) -> None:
        services = build_app_services()
        services.setup_guide_controller.set_active_session(
            replace(session(), mode=SessionMode.OPTICAL_METROLOGY)
        )
        opened = services.setup_guide_controller.open_current()
        window = opened.window

        result = window["on_action"]("UseGlobalCoordinates")

        self.assertEqual("success", result.status)
        self.assertEqual(1, window["render_count"])
        self.assertEqual("optional_origin_point", window["view_model"].active_stage_id)
        self.assertEqual(
            "optional_origin_point",
            services.setup_guide_controller.current_window["view_model"].active_stage_id,
        )

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
