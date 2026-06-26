import unittest
from dataclasses import replace

from metrology_process_planner.app.bootstrap import build_app_services
from metrology_process_planner.domains.session import SessionMode, SetupItemRecord, SetupState
from tests.editor_render_fixtures import session


class SetupGuideAlignmentCommandTests(unittest.TestCase):
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

    def test_optical_alignment_action_uses_explicit_modeless_command(self) -> None:
        services = build_app_services()
        services.setup_guide_controller.set_active_session(
            replace(session(), mode=SessionMode.OPTICAL_METROLOGY)
        )
        opened = services.setup_guide_controller.open_current()

        result = opened.window["on_action"]("StartOpticalAlignmentCapture")
        active = services.setup_guide_controller.active_session

        self.assertEqual("success", result.status)
        self.assertIsNotNone(active)
        self.assertEqual("alignment_box_capture", active.workflow.stage)
        self.assertEqual("site_box", active.workflow.active_primitive)
        self.assertEqual("setup:alignment_box_capture", active.workflow.pending_item_ref)
        refreshed = services.setup_guide_controller.open_current()
        stages = {stage.stage_id: stage for stage in refreshed.view_model.stages}
        self.assertEqual("waiting_for_canvas_capture", stages["optical_alignment"].status)

    def test_sem_alignment_action_uses_explicit_modeless_command(self) -> None:
        services = build_app_services()
        services.setup_guide_controller.set_active_session(
            replace(session(), mode=SessionMode.CDSEM_MEASUREMENT)
        )
        opened = services.setup_guide_controller.open_current()

        result = opened.window["on_action"]("StartSemAlignmentCapture")
        active = services.setup_guide_controller.active_session

        self.assertEqual("success", result.status)
        self.assertIsNotNone(active)
        self.assertEqual("sem_alignment_box_capture", active.workflow.stage)
        self.assertEqual("site_box", active.workflow.active_primitive)
        self.assertEqual("setup:sem_alignment_box_capture", active.workflow.pending_item_ref)
        refreshed = services.setup_guide_controller.open_current()
        stages = {stage.stage_id: stage for stage in refreshed.view_model.stages}
        self.assertEqual("waiting_for_canvas_capture", stages["sem_alignment"].status)

    def test_alignment_recapture_status_overrides_completed_setup_item(self) -> None:
        services = build_app_services()
        services.setup_guide_controller.set_active_session(
            replace(
                session(),
                mode=SessionMode.OPTICAL_METROLOGY,
                setup=SetupState(items=(_complete_alignment_item(),)),
            )
        )
        opened = services.setup_guide_controller.open_current()

        opened.window["on_action"]("StartOpticalAlignmentCapture")
        refreshed = services.setup_guide_controller.open_current()
        stages = {stage.stage_id: stage for stage in refreshed.view_model.stages}

        self.assertEqual("waiting_for_canvas_capture", stages["optical_alignment"].status)

def _complete_alignment_item() -> SetupItemRecord:
    return SetupItemRecord(
        "optical_alignment",
        "alignment_box_capture",
        "Optical Alignment Mark",
        "complete",
        metadata={"required": True},
    )


if __name__ == "__main__":
    unittest.main()
