import unittest
from dataclasses import replace

from metrology_process_planner.app.bootstrap import build_app_services
from metrology_process_planner.domains.session import (
    ModeDefinition,
    ModeRegistry,
    SessionMode,
    SetupDefinition,
    SetupItemRecord,
    SetupState,
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


class SetupGuideOptionalSkipCommandTestsPart2(unittest.TestCase):
    def test_optical_optional_setup_stages_can_be_skipped_in_sequence(self) -> None:
        services = build_app_services()
        services.setup_guide_controller.set_active_session(
            replace(session(), mode=SessionMode.OPTICAL_METROLOGY)
        )
        opened = services.setup_guide_controller.open_current()

        opened.window["on_action"]("UseGlobalCoordinates")
        first = opened.window["on_action"]("SkipOptionalSetupStage")
        second = opened.window["on_action"]("SkipOptionalSetupStage")
        active = services.setup_guide_controller.active_session

        self.assertEqual("success", first.status)
        self.assertEqual("success", second.status)
        self.assertIsNotNone(active)
        self.assertEqual(
            ("optional_origin_point", "origin_reference"),
            tuple(item.id for item in active.setup.items),
        )
        self.assertEqual(("skipped", "skipped"), tuple(item.status for item in active.setup.items))

    def test_skip_optional_setup_stage_targets_active_card_not_first_optional_item(self) -> None:
        services = build_app_services()
        source = replace(
            session(),
            mode=SessionMode.OPTICAL_METROLOGY,
            setup=SetupState(
                coordinate_mode="global",
                items=(
                    SetupItemRecord(
                        "origin_reference",
                        "origin_reference_box_capture",
                        "Origin Reference Image",
                        "active",
                        metadata={"required": False},
                    ),
                ),
            ),
        )
        services.setup_guide_controller.set_active_session(source)
        opened = services.setup_guide_controller.open_current()

        result = opened.window["on_action"]("SkipOptionalSetupStage")
        active = services.setup_guide_controller.active_session

        self.assertEqual("success", result.status)
        self.assertIsNotNone(active)
        self.assertEqual(
            ("origin_reference", "optional_origin_point"),
            tuple(item.id for item in active.setup.items),
        )
        self.assertEqual(("active", "skipped"), tuple(item.status for item in active.setup.items))

    def test_skip_optional_setup_stage_cannot_skip_required_alignment(self) -> None:
        services = build_app_services()
        source = replace(
            session(),
            mode=SessionMode.OPTICAL_METROLOGY,
            setup=SetupState(
                items=(
                    _skipped_item("optional_origin_point", "origin_point_capture"),
                    _skipped_item("origin_reference", "origin_reference_box_capture"),
                )
            ),
        )
        services.setup_guide_controller.set_active_session(source)
        opened = services.setup_guide_controller.open_current()

        result = opened.window["on_action"]("SkipOptionalSetupStage")
        active = services.setup_guide_controller.active_session

        self.assertEqual("blocked", result.status)
        self.assertIn("Optical Alignment Mark is required", result.message)
        self.assertIsNotNone(active)
        self.assertEqual(
            ("optional_origin_point", "origin_reference"),
            tuple(item.id for item in active.setup.items),
        )
