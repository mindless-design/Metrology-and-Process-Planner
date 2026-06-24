import json
import unittest
from pathlib import Path
from tempfile import TemporaryDirectory

from metrology_process_planner.app.bootstrap import build_app_services
from metrology_process_planner.app.commands import CommandId
from metrology_process_planner.persistence.paths import SessionPaths
from metrology_process_planner.workflows.editor import (
    EditorAction,
    EditorActionType,
    SessionDocumentBuilder,
    mark_metadata_edit,
    select_item,
)
from tests.editor_render_fixtures import empty_session, session, session_without_pending
from tests.measurement_child_fixtures import saved_capture_session


class SessionEditorCommandBridgeTests(unittest.TestCase):
    def test_reopen_setup_primary_action_routes_through_command_router(self) -> None:
        services = build_app_services()
        document = SessionDocumentBuilder().build(session_without_pending())
        result = services.session_editor_controller.open_document(document)

        action = _primary_action(result.window, EditorActionType.REOPEN_SETUP)
        result.window["on_primary_action"](action)

        routed = services.session_editor_controller.last_command_result
        self.assertIsNotNone(routed)
        self.assertEqual("success", routed.status)
        self.assertTrue(services.window_registry.is_open("setup-guide:session-001"))
        self.assertEqual("session-001", services.setup_guide_controller.active_session.id)

    def test_close_primary_action_routes_to_end_active_session(self) -> None:
        services = build_app_services()
        document = SessionDocumentBuilder().build(session_without_pending())
        result = services.session_editor_controller.open_document(document)

        action = _primary_action(result.window, EditorActionType.EXIT_SESSION)
        result.window["on_primary_action"](action)

        routed = services.session_editor_controller.last_command_result
        self.assertIsNotNone(routed)
        self.assertEqual("success", routed.status)
        self.assertIsNone(services.session_editor_controller.current_document)

    def test_close_primary_action_surfaces_blocked_session_lifecycle(self) -> None:
        services = build_app_services()
        document = SessionDocumentBuilder().build(session())
        result = services.session_editor_controller.open_document(document)

        action = _primary_action(result.window, EditorActionType.EXIT_SESSION)
        result.window["on_primary_action"](action)

        routed = services.session_editor_controller.last_command_result
        self.assertIsNotNone(routed)
        self.assertEqual("blocked", routed.status)
        self.assertIsNotNone(services.session_editor_controller.current_document)

    def test_save_primary_action_routes_through_session_command(self) -> None:
        services = build_app_services()
        with TemporaryDirectory() as temp_dir:
            paths = SessionPaths.for_folder(Path(temp_dir))
            document = SessionDocumentBuilder().build(empty_session())
            document = mark_metadata_edit(document, "dashboard", "name", "Renamed")
            result = services.session_editor_controller.open_document(document, paths)

            action = _primary_action(result.window, EditorActionType.SAVE_EDITS)
            result.window["on_primary_action"](action)

            routed = services.session_editor_controller.last_command_result
            self.assertIsNotNone(routed)
            self.assertEqual(CommandId.SAVE_SESSION_EDITS, routed.command_id)
            self.assertEqual("success", routed.status)
            self.assertEqual("session-001", routed.updated_document_id)
            current = services.session_editor_controller.current_document
            self.assertIsNotNone(current)
            self.assertFalse(current.dirty_state.is_dirty)
            payload = json.loads(paths.session_json.read_text(encoding="utf-8"))
            self.assertEqual("Renamed", payload["session"]["name"])

    def test_save_session_command_reports_unavailable_without_active_document(self) -> None:
        services = build_app_services()

        routed = services.command_router.route(CommandId.SAVE_SESSION_EDITS)

        self.assertEqual("unavailable", routed.status)
        self.assertIn("No active session editor document", routed.message)

    def test_pending_save_action_routes_through_capture_command(self) -> None:
        services = build_app_services()
        document = SessionDocumentBuilder().build(session())
        result = services.session_editor_controller.open_document(document)

        action = _inspector_action(result.window, EditorActionType.PENDING_SAVE)
        result.window["on_action"](action)

        routed = services.session_editor_controller.last_command_result
        current = services.session_editor_controller.current_document
        self.assertIsNotNone(routed)
        self.assertEqual(CommandId.SAVE_PENDING_CAPTURE, routed.command_id)
        self.assertEqual("success", routed.status)
        self.assertIsNotNone(current)
        self.assertEqual((), current.session.pending_captures)

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


def _primary_action(window, action_type: EditorActionType) -> EditorAction:
    return next(action for action in window["primary_actions"] if action.action_type is action_type)


def _inspector_action(window, action_type: EditorActionType) -> EditorAction:
    return next(action for action in window["actions"] if action.action_type is action_type)


if __name__ == "__main__":
    unittest.main()
