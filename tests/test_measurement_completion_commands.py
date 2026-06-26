import tempfile
import unittest
from pathlib import Path

from metrology_process_planner.app.bootstrap import build_app_services
from metrology_process_planner.app.commands import CommandId
from metrology_process_planner.domains.session import CanvasVisualFlag
from metrology_process_planner.persistence.paths import SessionPaths
from tests.measurement_child_fixtures import saved_measurement_document


class MeasurementCompletionCommandTests(unittest.TestCase):
    def test_take_another_measurement_prompt_choice_routes_through_command(self) -> None:
        services = build_app_services()
        _open_saved_measurement_document(services)

        routed = services.command_router.route(CommandId.TAKE_ANOTHER_MEASUREMENT)

        current = services.session_editor_controller.current_document
        self.assertEqual("success", routed.status)
        self.assertIsNotNone(current)
        self.assertEqual("capture:cap-001", routed.selected_item_id)
        self.assertTrue(current.session.workflow.active)
        self.assertEqual("measurement", current.session.workflow.active_primitive)

    def test_return_to_editor_prompt_choice_routes_through_global_command(self) -> None:
        services = build_app_services()
        _open_saved_measurement_document(services)

        routed = services.command_router.route(CommandId.RETURN_TO_EDITOR)

        current = services.session_editor_controller.current_document
        self.assertEqual("success", routed.status)
        self.assertIsNotNone(current)
        self.assertEqual("capture:cap-001", routed.selected_item_id)
        self.assertFalse(current.session.workflow.active)
        self.assertNotIn(
            CanvasVisualFlag.ACTIVE_PARENT,
            current.session.canvas_objects[0].visual_state,
        )

    def test_done_prompt_choice_routes_through_command(self) -> None:
        services = build_app_services()
        _open_saved_measurement_document(services)

        routed = services.command_router.route(CommandId.DONE)

        current = services.session_editor_controller.current_document
        self.assertEqual("success", routed.status)
        self.assertIsNotNone(current)
        self.assertEqual("measurement:meas-001", routed.selected_item_id)
        self.assertFalse(current.session.workflow.active)


def _open_saved_measurement_document(services) -> None:
    with tempfile.TemporaryDirectory() as temp_dir:
        paths = SessionPaths.for_folder(Path(temp_dir))
        paths.ensure_created()
        document = saved_measurement_document(paths)
        services.session_editor_controller.open_document(document, paths)


if __name__ == "__main__":
    unittest.main()
