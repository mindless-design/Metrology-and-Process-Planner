import unittest
from dataclasses import replace

from metrology_process_planner.app.bootstrap import build_app_services
from metrology_process_planner.domains.session import SessionMode, SetupItemRecord, SetupState
from tests.editor_render_fixtures import session


def _complete_item(item_id: str) -> SetupItemRecord:
    return SetupItemRecord(
        item_id,
        "alignment_box_capture",
        "Optical Alignment Mark",
        "complete",
        metadata={"required": True},
    )

if __name__ == "__main__":
    unittest.main()


class SetupGuideRequiredStageTestsPart2(unittest.TestCase):
    def test_ready_card_can_mark_complete_after_required_setup_is_done(self) -> None:
        services = build_app_services()
        source = replace(
            session(),
            mode=SessionMode.OPTICAL_METROLOGY,
            setup=SetupState(items=(_complete_item("optical_alignment"),)),
        )
        services.setup_guide_controller.set_active_session(source)

        opened = services.setup_guide_controller.open_current()
        ready = next(
            stage for stage in opened.view_model.stages
            if stage.stage_id == "ready_for_capture"
        )

        self.assertIsNotNone(ready.primary_action_view)
        assert ready.primary_action_view is not None
        self.assertTrue(ready.primary_action_view.enabled)
        self.assertEqual("", ready.primary_action_view.disabled_reason)

    def test_valid_ready_flag_bypasses_unfinished_optional_setup_cards(self) -> None:
        services = build_app_services()
        source = replace(
            session(),
            mode=SessionMode.OPTICAL_METROLOGY,
            setup=SetupState(
                is_capture_ready=True,
                items=(_complete_item("optical_alignment"),),
            ),
        )
        services.setup_guide_controller.set_active_session(source)

        opened = services.setup_guide_controller.open_current()

        self.assertEqual("setup_ready", opened.view_model.status)
        self.assertEqual("ready_for_capture", opened.view_model.active_stage_id)

    def test_ready_recipe_free_setup_explains_disabled_mark_complete_action(self) -> None:
        services = build_app_services()
        source = replace(
            session(),
            mode=SessionMode.OPTICAL_METROLOGY,
            setup=SetupState(
                is_capture_ready=True,
                items=(_complete_item("optical_alignment"),),
            ),
        )
        services.setup_guide_controller.set_active_session(source)

        opened = services.setup_guide_controller.open_current()
        ready = next(
            stage for stage in opened.view_model.stages
            if stage.stage_id == "ready_for_capture"
        )

        self.assertIsNotNone(ready.primary_action_view)
        assert ready.primary_action_view is not None
        self.assertFalse(ready.primary_action_view.enabled)
        self.assertEqual(
            "Setup is already ready for capture.",
            ready.primary_action_view.disabled_reason,
        )

    def test_optical_partial_setup_still_shows_all_declared_cards(self) -> None:
        services = build_app_services()
        source = replace(
            session(),
            mode=SessionMode.OPTICAL_METROLOGY,
            setup=SetupState(items=(_complete_item("optical_alignment"),)),
        )
        services.setup_guide_controller.set_active_session(source)

        opened = services.setup_guide_controller.open_current()
        stages = {stage.stage_id: stage for stage in opened.view_model.stages}

        self.assertEqual(
            (
                "origin_choice",
                "optional_origin_point",
                "origin_reference",
                "optical_alignment",
                "ready_for_capture",
            ),
            tuple(stages),
        )
        self.assertEqual("complete", stages["optical_alignment"].status)
        self.assertEqual("required", stages["optical_alignment"].requirement_badge)
        self.assertEqual("blocked", stages["ready_for_capture"].status)
