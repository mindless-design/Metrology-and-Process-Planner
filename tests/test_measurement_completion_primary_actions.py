import unittest
from pathlib import Path
from tempfile import TemporaryDirectory

from metrology_process_planner.app.bootstrap import build_app_services
from metrology_process_planner.app.commands import CommandId
from metrology_process_planner.persistence.paths import SessionPaths
from metrology_process_planner.workflows.editor import EditorAction, EditorActionType
from tests.measurement_child_fixtures import saved_measurement_document


class MeasurementCompletionPrimaryActionTests(unittest.TestCase):
    def test_primary_action_routes_take_another_measurement_command(self) -> None:
        services = build_app_services()
        with TemporaryDirectory() as temp_dir:
            paths = SessionPaths.for_folder(Path(temp_dir))
            document = saved_measurement_document(paths)
            result = services.session_editor_controller.open_document(document, paths)

            action = _primary_action(result.window, EditorActionType.TAKE_ANOTHER_MEASUREMENT)
            result.window["on_primary_action"](action)

        routed = services.session_editor_controller.last_command_result
        current = services.session_editor_controller.current_document
        self.assertIsNotNone(routed)
        self.assertEqual(CommandId.TAKE_ANOTHER_MEASUREMENT, routed.command_id)
        self.assertEqual("success", routed.status)
        self.assertIsNotNone(current)
        self.assertTrue(current.session.workflow.active)
        self.assertEqual("measurement", current.session.workflow.active_primitive)

    def test_primary_action_routes_return_to_editor_command(self) -> None:
        services = build_app_services()
        with TemporaryDirectory() as temp_dir:
            paths = SessionPaths.for_folder(Path(temp_dir))
            document = saved_measurement_document(paths)
            result = services.session_editor_controller.open_document(document, paths)

            action = _primary_action(result.window, EditorActionType.RETURN_TO_EDITOR)
            result.window["on_primary_action"](action)

        routed = services.session_editor_controller.last_command_result
        current = services.session_editor_controller.current_document
        self.assertIsNotNone(routed)
        self.assertEqual(CommandId.RETURN_TO_EDITOR, routed.command_id)
        self.assertEqual("success", routed.status)
        self.assertEqual("capture:cap-001", routed.selected_item_id)
        self.assertIsNotNone(current)
        self.assertFalse(current.session.workflow.active)
        self.assertEqual("capture:cap-001", current.selection.selected_item_id)

    def test_primary_action_routes_done_command(self) -> None:
        services = build_app_services()
        with TemporaryDirectory() as temp_dir:
            paths = SessionPaths.for_folder(Path(temp_dir))
            document = saved_measurement_document(paths)
            result = services.session_editor_controller.open_document(document, paths)

            action = _primary_action(result.window, EditorActionType.DONE)
            result.window["on_primary_action"](action)

        routed = services.session_editor_controller.last_command_result
        current = services.session_editor_controller.current_document
        self.assertIsNotNone(routed)
        self.assertEqual(CommandId.DONE, routed.command_id)
        self.assertEqual("success", routed.status)
        self.assertEqual("measurement:meas-001", routed.selected_item_id)
        self.assertIsNotNone(current)
        self.assertFalse(current.session.workflow.active)
        self.assertEqual("measurement:meas-001", current.selection.selected_item_id)


def _primary_action(window, action_type: EditorActionType) -> EditorAction:
    return next(action for action in window["primary_actions"] if action.action_type is action_type)


if __name__ == "__main__":
    unittest.main()
