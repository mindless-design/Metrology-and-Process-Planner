import unittest
from dataclasses import replace

from metrology_process_planner.app.bootstrap import build_app_services
from metrology_process_planner.app.commands import CommandId
from metrology_process_planner.domains.session import SessionMode
from metrology_process_planner.workflows.editor import (
    DefaultSessionModeAdapter,
    EditorActionType,
    SessionDocumentBuilder,
    select_item,
)
from tests.measurement_child_fixtures import saved_capture_session


class MeasurementModePolicyTests(unittest.TestCase):
    def test_simple_capture_exposes_add_measurement(self) -> None:
        document = SessionDocumentBuilder().build(saved_capture_session())
        item = document.items_by_id["capture:cap-001"]

        actions = DefaultSessionModeAdapter().actions(document.session, item)

        self.assertIn(EditorActionType.ADD_MEASUREMENT, {action.action_type for action in actions})

    def test_recipe_free_capture_modes_expose_and_route_add_measurement(self) -> None:
        for mode in _RECIPE_FREE_MEASUREMENT_MODES:
            with self.subTest(mode=mode.value):
                services = build_app_services()
                source = replace(saved_capture_session(), mode=mode)
                document = select_item(SessionDocumentBuilder().build(source), "capture:cap-001")
                services.session_editor_controller.open_document(document)

                actions = DefaultSessionModeAdapter().actions(
                    document.session,
                    document.items_by_id["capture:cap-001"],
                )
                routed = services.command_router.route(CommandId.ADD_MEASUREMENT)
                current = services.session_editor_controller.current_document

                self.assertIn(
                    EditorActionType.ADD_MEASUREMENT,
                    {action.action_type for action in actions},
                )
                self.assertEqual("success", routed.status)
                self.assertIsNotNone(current)
                assert current is not None
                self.assertTrue(current.session.workflow.active)
                self.assertEqual("measurement_line", current.session.workflow.stage)
                self.assertEqual("capture:cap-001", current.session.workflow.pending_item_ref)

    def test_mode_without_measurement_support_hides_add_measurement(self) -> None:
        source = replace(saved_capture_session(), mode=SessionMode.PROCESS_FLOW_SUMMARY)
        document = SessionDocumentBuilder().build(source)
        item = document.items_by_id["capture:cap-001"]

        actions = DefaultSessionModeAdapter().actions(document.session, item)

        self.assertNotIn(
            EditorActionType.ADD_MEASUREMENT,
            {action.action_type for action in actions},
        )

    def test_add_measurement_command_rejects_mode_without_measurement_support(self) -> None:
        services = build_app_services()
        source = replace(saved_capture_session(), mode=SessionMode.PROCESS_FLOW_SUMMARY)
        document = select_item(SessionDocumentBuilder().build(source), "capture:cap-001")
        services.session_editor_controller.open_document(document)

        routed = services.command_router.route(CommandId.ADD_MEASUREMENT)

        current = services.session_editor_controller.current_document
        self.assertEqual("unavailable", routed.status)
        self.assertIsNotNone(current)
        self.assertFalse(current.session.workflow.active)
        self.assertIn("does not support measurements", routed.message)


_RECIPE_FREE_MEASUREMENT_MODES = (
    SessionMode.SIMPLE_CAPTURE,
    SessionMode.SIMPLE_LABELED_CAPTURE,
    SessionMode.FAST_BATCH_CAPTURE,
    SessionMode.CAD_REVIEW,
    SessionMode.CAD_REVIEW_CAPTURE,
    SessionMode.OPTICAL_METROLOGY,
    SessionMode.CDSEM_CAPTURE,
    SessionMode.CDSEM_MEASUREMENT,
    SessionMode.GRID_MEASUREMENT,
)


if __name__ == "__main__":
    unittest.main()
