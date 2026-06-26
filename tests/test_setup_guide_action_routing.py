import unittest
from dataclasses import replace

from metrology_process_planner.app.bootstrap import build_app_services
from metrology_process_planner.app.commands import CommandId, command_id_from_view_action
from metrology_process_planner.domains.session import SessionMode
from tests.editor_render_fixtures import session


class SetupGuideActionRoutingTests(unittest.TestCase):
    def test_optical_and_cdsem_visible_actions_resolve_to_registered_commands(self) -> None:
        for mode in (
            SessionMode.OPTICAL_METROLOGY,
            SessionMode.CDSEM_MEASUREMENT,
            SessionMode.CDSEM_PLANNING,
        ):
            with self.subTest(mode=mode.value):
                services = build_app_services()
                services.setup_guide_controller.set_active_session(
                    replace(session(), mode=mode)
                )

                opened = services.setup_guide_controller.open_current()
                command_ids = {
                    command_id_from_view_action(action_id)
                    for action_id in _visible_action_ids(opened.view_model)
                }

                self.assertTrue(command_ids)
                self.assertLessEqual(command_ids, set(services.commands.specs))

    def test_optical_and_cdsem_setup_actions_stay_recipe_free(self) -> None:
        forbidden = {
            "AttachRecipe",
            "ValidateRecipeContext",
            "OpenRecipe",
            "OpenRecipeEditor",
        }
        shared_expected = {
            "UseGlobalCoordinates",
            "UseOriginCoordinates",
            "StartOriginReferenceCapture",
            "StartOpticalAlignmentCapture",
            "SkipOptionalSetupStage",
            "MarkSetupComplete",
            "ReturnToEditor",
        }
        expected_by_mode = {
            SessionMode.OPTICAL_METROLOGY: shared_expected | {"StartOriginPointCapture"},
            SessionMode.CDSEM_MEASUREMENT: shared_expected | {"StartSemAlignmentCapture"},
            SessionMode.CDSEM_PLANNING: shared_expected | {"StartSemAlignmentCapture"},
        }
        for mode in (
            SessionMode.OPTICAL_METROLOGY,
            SessionMode.CDSEM_MEASUREMENT,
            SessionMode.CDSEM_PLANNING,
        ):
            with self.subTest(mode=mode.value):
                services = build_app_services()
                services.setup_guide_controller.set_active_session(
                    replace(session(), mode=mode)
                )

                opened = services.setup_guide_controller.open_current()
                action_ids = set(_visible_action_ids(opened.view_model))

                self.assertTrue(forbidden.isdisjoint(action_ids))
                self.assertLessEqual(expected_by_mode[mode], action_ids)

    def test_unknown_setup_action_returns_structured_unavailable(self) -> None:
        services = build_app_services()
        services.setup_guide_controller.set_active_session(
            replace(session(), mode=SessionMode.OPTICAL_METROLOGY)
        )
        opened = services.setup_guide_controller.open_current()

        result = opened.window["on_action"]("StartRecipeSolverDance")

        self.assertEqual(CommandId.OPEN_SETUP_GUIDE, result.command_id)
        self.assertEqual("unavailable", result.status)
        self.assertIn("Unknown setup guide action", result.message)
        self.assertEqual(result, services.setup_guide_controller.last_action_result)


def _visible_action_ids(view_model) -> tuple[str, ...]:
    action_ids: list[str] = []
    for stage in view_model.stages:
        if stage.primary_action:
            action_ids.append(stage.primary_action)
        action_ids.extend(stage.secondary_actions)
    action_ids.extend(view_model.available_commands)
    action_ids.extend(action.command_id for action in view_model.action_views)
    return tuple(sorted(set(action_ids)))


if __name__ == "__main__":
    unittest.main()
