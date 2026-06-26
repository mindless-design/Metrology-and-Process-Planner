import unittest
from dataclasses import replace
from pathlib import Path
from tempfile import TemporaryDirectory

from metrology_process_planner.app.bootstrap import build_app_services
from metrology_process_planner.app.commands import CommandId
from metrology_process_planner.domains.session import SessionMode
from metrology_process_planner.persistence.paths import SessionPaths
from metrology_process_planner.workflows.editor import (
    EditorAction,
    EditorActionDispatcher,
    EditorActionType,
    SessionDocumentBuilder,
    mark_metadata_edit,
    select_item,
)
from tests.editor_render_fixtures import empty_session, session_without_pending
from tests.measurement_child_fixtures import (
    document_with_pending_measurement,
    measurement_metadata_edits,
    saved_capture_session,
)


def _primary_action(window, action_type: EditorActionType) -> EditorAction:
    return next(action for action in window["primary_actions"] if action.action_type is action_type)

def _inspector_action(window, action_type: EditorActionType) -> EditorAction:
    return next(action for action in window["actions"] if action.action_type is action_type)

if __name__ == "__main__":
    unittest.main()


class SessionEditorCommandBridgeTestsPart2(unittest.TestCase):
    def test_add_measurement_command_uses_selected_capture_item(self) -> None:
        services = build_app_services()
        document = SessionDocumentBuilder().build(saved_capture_session())
        document = select_item(document, "capture:cap-001")
        services.session_editor_controller.open_document(document)

        routed = services.command_router.route(CommandId.ADD_MEASUREMENT)

        current = services.session_editor_controller.current_document
        self.assertEqual("success", routed.status)
        self.assertEqual("session-001", routed.updated_document_id)
        self.assertIsNotNone(current)
        self.assertEqual("measurement_line", current.session.workflow.stage)
        self.assertEqual("measurement", current.session.workflow.active_primitive)

    def test_save_measurement_command_preserves_completion_prompt(self) -> None:
        services = build_app_services()
        with TemporaryDirectory() as temp_dir:
            paths = SessionPaths.for_folder(Path(temp_dir))
            paths.ensure_created()
            document = measurement_metadata_edits(
                document_with_pending_measurement(saved_capture_session())
            )
            document = select_item(document, "measurement:meas-001")
            services.session_editor_controller.open_document(document, paths)

            routed = services.command_router.route(CommandId.SAVE_MEASUREMENT)

        self.assertIn(routed.status, {"success", "warning"})
        self.assertIsNotNone(routed.post_action_prompt)
        self.assertEqual(
            (
                ("take_another_measurement", "Take Another Measurement"),
                ("return_to_editor", "Return to Editor"),
                ("done", "Done"),
            ),
            routed.post_action_prompt.choices,
        )

    def test_add_capture_primary_action_routes_to_shared_capture_command(self) -> None:
        services = build_app_services()
        document = SessionDocumentBuilder().build(
            replace(empty_session(), mode=SessionMode.SIMPLE_CAPTURE)
        )
        result = services.session_editor_controller.open_document(document)

        action = _primary_action(result.window, EditorActionType.ADD_CAPTURE)
        result.window["on_primary_action"](action)

        routed = services.session_editor_controller.last_command_result
        current = services.session_editor_controller.current_document
        self.assertIsNotNone(routed)
        self.assertEqual(CommandId.START_CAPTURE, routed.command_id)
        self.assertEqual("success", routed.status)
        self.assertIsNotNone(current)
        self.assertEqual("box_capture", current.session.workflow.stage)
        self.assertEqual("site_box", current.session.workflow.active_primitive)

    def test_discard_unsaved_edits_command_clears_dirty_state(self) -> None:
        services = build_app_services()
        document = SessionDocumentBuilder().build(empty_session())
        document = mark_metadata_edit(document, "dashboard", "name", "Unsaved")
        services.session_editor_controller.open_document(document)

        routed = services.command_router.route(CommandId.DISCARD_UNSAVED_EDITS)

        current = services.session_editor_controller.current_document
        self.assertEqual("success", routed.status)
        self.assertIsNotNone(current)
        self.assertFalse(current.dirty_state.is_dirty)
        self.assertEqual("Demo", current.session.name)

    def test_inline_metadata_update_dispatch_marks_document_dirty(self) -> None:
        document = select_item(
            SessionDocumentBuilder().build(session_without_pending()),
            "capture:cap-001",
        )

        result = EditorActionDispatcher().dispatch(
            document,
            EditorAction(
                EditorActionType.UPDATE_METADATA_FIELD,
                "Update Metadata",
                "capture:cap-001",
                payload=(("field_key", "label"), ("value", "Inline Site")),
            ),
        )

        self.assertEqual("success", result.status)
        self.assertTrue(result.document.dirty_state.is_dirty)
        self.assertEqual(
            (("capture:cap-001", "label", "Inline Site"),),
            result.document.dirty_state.unsaved_metadata_edits,
        )
