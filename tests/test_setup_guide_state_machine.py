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
        self.assertIn("StartOriginPointCapture", first.available_commands)
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

    def test_setup_cards_preserve_action_labels_and_disabled_reasons(self) -> None:
        stage = SetupGuidePresenter().build(_disabled_action_session()).stages[0]

        self.assertIsNotNone(stage.primary_action_view)
        assert stage.primary_action_view is not None
        self.assertEqual("Validate Recipe", stage.primary_action_view.label)
        self.assertFalse(stage.primary_action_view.enabled)
        self.assertEqual("Attach a recipe first.", stage.primary_action_view.disabled_reason)
        self.assertEqual(
            ("Attach Recipe", "Mark Ready"),
            tuple(action.label for action in stage.secondary_action_views),
        )
        self.assertFalse(stage.secondary_action_views[1].enabled)
        self.assertEqual(
            "Validation is required.",
            stage.secondary_action_views[1].disabled_reason,
        )

    def test_setup_guide_exposes_footer_action_view_models(self) -> None:
        view_model = SetupGuidePresenter().build(session())

        actions = {action.command_id: action for action in view_model.action_views}

        self.assertEqual("Start Origin Capture", actions["StartOriginPointCapture"].label)
        self.assertEqual("Return to Editor", actions["ReturnToEditor"].label)
        self.assertEqual("Close", actions["CloseSetupGuide"].label)
        self.assertEqual(
            "Capture an origin point when local coordinates are needed.",
            view_model.status_message,
        )

    def test_state_machine_reports_ready_when_setup_is_capture_ready(self) -> None:
        source = replace(session(), setup=SetupState(is_capture_ready=True))

        snapshot = SetupGuideStateMachine().evaluate(source)

        self.assertEqual(SetupGuideState.SETUP_READY, snapshot.state)
        self.assertEqual(SetupStageStatus.COMPLETE, snapshot.stages[-1].status)

def _disabled_action_session():
    return replace(
        session(),
        setup=SetupState(
            items=(
                SetupItemRecord(
                    "stage-1",
                    "recipe_validate",
                    "Recipe Validation",
                    "blocked",
                    metadata=_disabled_action_metadata(),
                ),
            )
        ),
    )


def _disabled_action_metadata():
    return {
        "required": True,
        "description": "Validate the attached process recipe.",
        "primary_action": "ValidateRecipeContext",
        "primary_action_label": "Validate Recipe",
        "primary_action_enabled": False,
        "primary_action_disabled_reason": "Attach a recipe first.",
        "secondary_actions": [
            {"command_id": "AttachRecipe", "label": "Attach Recipe"},
            {
                "command_id": "MarkSetupComplete",
                "label": "Mark Ready",
                "enabled": False,
                "disabled_reason": "Validation is required.",
            },
        ],
    }


if __name__ == "__main__":
    unittest.main()
