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


class SetupGuideRequiredStageTestsPart3(unittest.TestCase):
    def test_cdsem_partial_setup_still_shows_required_sem_alignment(self) -> None:
        services = build_app_services()
        source = replace(
            session(),
            mode=SessionMode.CDSEM_CAPTURE,
            setup=SetupState(items=(_complete_item("optical_alignment"),)),
        )
        services.setup_guide_controller.set_active_session(source)

        opened = services.setup_guide_controller.open_current()
        stages = {stage.stage_id: stage for stage in opened.view_model.stages}

        self.assertEqual("complete", stages["optical_alignment"].status)
        self.assertEqual("active", stages["sem_alignment"].status)
        self.assertEqual("required", stages["sem_alignment"].requirement_badge)
        self.assertEqual("StartSemAlignmentCapture", stages["sem_alignment"].primary_action)
