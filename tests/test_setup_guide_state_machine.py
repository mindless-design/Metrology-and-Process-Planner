import unittest
from dataclasses import replace

from metrology_process_planner.domains.geometry import Point
from metrology_process_planner.domains.session import (
    OriginRecord,
    SessionMode,
    SetupItemRecord,
    SetupState,
)
from metrology_process_planner.ui.setup_guide import SetupGuidePresenter
from metrology_process_planner.workflows.setup_guide_state import (
    SetupGuideState,
    SetupGuideStateMachine,
    SetupStageStatus,
)
from tests.editor_render_fixtures import empty_session, session


class SetupGuideStateMachineTests(unittest.TestCase):
    def test_missing_session_requests_session_without_blocking_dialog(self) -> None:
        view_model = SetupGuidePresenter().build(None)

        self.assertEqual("session_required", view_model.status)
        self.assertEqual("open_session", view_model.active_stage_id)
        self.assertEqual(("OpenSession",), view_model.available_commands)
        self.assertEqual("Open Session", view_model.next_action)

    def test_default_setup_reconstructs_active_stage_from_session(self) -> None:
        first = SetupGuidePresenter().build(session())
        reopened = SetupGuidePresenter().build(session())

        self.assertEqual(first.active_stage_id, reopened.active_stage_id)
        self.assertEqual("origin", first.active_stage_id)
        self.assertIn("StartOriginCapture", first.available_commands)
        self.assertIn("ReturnToEditor", first.available_commands)
        self.assertEqual("Capture or accept origin", first.current_stage_label)

    def test_mode_declared_process_stages_surface_recipe_warning(self) -> None:
        source = replace(
            empty_session(),
            mode=SessionMode.PROFILOMETRY_PLANNER,
            setup=SetupState(
                origin=OriginRecord(Point(0, 0)),
                is_capture_ready=False,
            ),
        )

        view_model = SetupGuidePresenter().build(source)

        self.assertEqual("recipe_warning", view_model.status)
        self.assertEqual("recipe_context", view_model.active_stage_id)
        self.assertEqual("Profilometry Planner", view_model.mode_display_name)
        self.assertIn("AttachRecipe", view_model.available_commands)
        stages = {stage.stage_id: stage for stage in view_model.stages}
        self.assertEqual("warning", stages["recipe_context"].status)
        self.assertEqual("recipe_select", stages["recipe_context"].stage_type)

    def test_custom_setup_items_render_as_generic_cards(self) -> None:
        source = replace(
            session(),
            setup=SetupState(
                items=(
                    SetupItemRecord(
                        "stage-1",
                        "alignment_box_capture",
                        "Optical Alignment",
                        "active",
                        metadata={
                            "required": True,
                            "description": "Capture the optical alignment mark.",
                            "primary_action": "StartAlignmentCapture",
                            "primary_action_label": "Start Alignment Capture",
                            "secondary_actions": ["SkipOptionalSetupStage"],
                        },
                    ),
                )
            ),
        )

        view_model = SetupGuidePresenter().build(source)

        self.assertEqual("stage-1", view_model.active_stage_id)
        self.assertEqual("alignment_required", view_model.status)
        self.assertEqual("StartAlignmentCapture", view_model.stages[0].primary_action)
        self.assertEqual(("SkipOptionalSetupStage",), view_model.stages[0].secondary_actions)

    def test_state_machine_reports_ready_when_setup_is_capture_ready(self) -> None:
        source = replace(session(), setup=SetupState(is_capture_ready=True))

        snapshot = SetupGuideStateMachine().evaluate(source)

        self.assertEqual(SetupGuideState.SETUP_READY, snapshot.state)
        self.assertEqual(SetupStageStatus.COMPLETE, snapshot.stages[-1].status)


if __name__ == "__main__":
    unittest.main()
