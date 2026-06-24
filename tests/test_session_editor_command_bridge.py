import unittest

from metrology_process_planner.app.bootstrap import build_app_services
from metrology_process_planner.workflows.editor import (
    EditorAction,
    EditorActionType,
    SessionDocumentBuilder,
)
from tests.editor_render_fixtures import session, session_without_pending


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


def _primary_action(window, action_type: EditorActionType) -> EditorAction:
    return next(action for action in window["primary_actions"] if action.action_type is action_type)


if __name__ == "__main__":
    unittest.main()
