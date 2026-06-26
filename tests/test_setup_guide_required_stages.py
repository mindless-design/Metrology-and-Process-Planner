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


class SetupGuideRequiredStageTestsPart1(unittest.TestCase):
    def test_required_optical_alignment_blocks_setup_ready(self) -> None:
        services = build_app_services()
        services.setup_guide_controller.set_active_session(
            replace(session(), mode=SessionMode.OPTICAL_METROLOGY)
        )
        opened = services.setup_guide_controller.open_current()

        result = opened.window["on_action"]("MarkSetupComplete")
        active = services.setup_guide_controller.active_session

        self.assertEqual("blocked", result.status)
        self.assertIn("Optical Alignment Mark", result.message)
        self.assertIsNotNone(active)
        self.assertFalse(active.setup.is_capture_ready)

    def test_ready_card_locks_mark_complete_until_required_setup_is_done(self) -> None:
        services = build_app_services()
        services.setup_guide_controller.set_active_session(
            replace(session(), mode=SessionMode.CDSEM_CAPTURE)
        )

        opened = services.setup_guide_controller.open_current()
        ready = next(
            stage for stage in opened.view_model.stages
            if stage.stage_id == "ready_for_capture"
        )

        self.assertIsNotNone(ready.primary_action_view)
        assert ready.primary_action_view is not None
        self.assertFalse(ready.primary_action_view.enabled)
        self.assertEqual(
            "Complete required setup cards first: Optical Alignment Mark, SEM Alignment Mark.",
            ready.primary_action_view.disabled_reason,
        )

    def test_stale_ready_flag_does_not_bypass_required_optical_alignment(self) -> None:
        services = build_app_services()
        source = replace(
            session(),
            mode=SessionMode.OPTICAL_METROLOGY,
            setup=SetupState(is_capture_ready=True),
        )
        services.setup_guide_controller.set_active_session(source)

        opened = services.setup_guide_controller.open_current()
        stages = {stage.stage_id: stage for stage in opened.view_model.stages}

        self.assertEqual("origin_point_required", opened.view_model.status)
        self.assertEqual("optional_origin_point", opened.view_model.active_stage_id)
        self.assertEqual("active", stages["optical_alignment"].status)
        self.assertEqual("blocked", stages["ready_for_capture"].status)

    def test_required_cdsem_sem_alignment_blocks_setup_ready(self) -> None:
        services = build_app_services()
        source = replace(
            session(),
            mode=SessionMode.CDSEM_CAPTURE,
            setup=SetupState(items=(_complete_item("optical_alignment"),)),
        )
        services.setup_guide_controller.set_active_session(source)
        opened = services.setup_guide_controller.open_current()

        result = opened.window["on_action"]("MarkSetupComplete")

        self.assertEqual("blocked", result.status)
        self.assertIn("SEM Alignment Mark", result.message)

    def test_completed_required_alignment_allows_setup_ready(self) -> None:
        services = build_app_services()
        source = replace(
            session(),
            mode=SessionMode.OPTICAL_METROLOGY,
            setup=SetupState(items=(_complete_item("optical_alignment"),)),
        )
        services.setup_guide_controller.set_active_session(source)
        opened = services.setup_guide_controller.open_current()

        result = opened.window["on_action"]("MarkSetupComplete")
        active = services.setup_guide_controller.active_session

        self.assertEqual("success", result.status)
        self.assertIsNotNone(active)
        self.assertTrue(active.setup.is_capture_ready)
