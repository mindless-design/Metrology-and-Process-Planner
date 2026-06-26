import unittest

from metrology_process_planner.app.bootstrap import build_app_services
from metrology_process_planner.app.commands import CommandId
from metrology_process_planner.app.session_editor import SessionEditorController
from metrology_process_planner.domains.session import SessionMode, SessionRecord
from metrology_process_planner.ui.session_editor import (
    InMemorySessionEditorWidgetFactory,
    SessionEditorCallbacks,
    SessionEditorShell,
)
from metrology_process_planner.workflows.editor import (
    DefaultSessionModeAdapter,
    EditorAction,
    EditorActionType,
    SessionDocumentBuilder,
)
from tests.editor_render_fixtures import (
    empty_session,
    session_without_pending,
)
from tests.editor_render_fixtures import session as rich_session


def _document():
    session = SessionRecord(
        id="session-001",
        name="Demo",
        mode=SessionMode.SIMPLE_CAPTURE,
        created_at="2026-06-23T20:00:00Z",
        updated_at="2026-06-23T20:00:00Z",
    )
    return SessionDocumentBuilder().build(session, raw_payload=session.to_dict())

if __name__ == "__main__":
    unittest.main()


class SessionEditorShellControllerTestsPart2(unittest.TestCase):
    def test_shell_exposes_inline_metadata_controls(self) -> None:
        document = SessionDocumentBuilder().build(session_without_pending())
        controller = SessionEditorController(
            shell=SessionEditorShell(InMemorySessionEditorWidgetFactory())
        )

        result = controller.open_document(document)
        result.window["on_select"]("capture:cap-001")
        result.window["on_metadata_change"]("label", "Inline Site")

        controls = {
            control["key"]: control
            for control in result.window["metadata_controls"]
        }
        self.assertEqual("text", controls["label"]["control_type"])
        self.assertEqual("label", controls["center"]["control_type"])
        self.assertTrue(controller.current_document.dirty_state.is_dirty)
        self.assertIn(("label", "Label", "Inline Site"), result.window["fields"])

    def test_controller_raises_existing_window_for_same_session(self) -> None:
        document = SessionDocumentBuilder().build(rich_session())
        controller = SessionEditorController(
            shell=SessionEditorShell(InMemorySessionEditorWidgetFactory())
        )

        first = controller.open_document(document)
        second = controller.open_document(document)

        self.assertEqual("opened", first.status)
        self.assertEqual("raised", second.status)
        self.assertIs(first.window, second.window)
        self.assertEqual(1, second.window["raised"])

    def test_controller_rerenders_shell_after_mutating_action_callback(self) -> None:
        document = SessionDocumentBuilder().build(rich_session())
        controller = SessionEditorController(
            shell=SessionEditorShell(InMemorySessionEditorWidgetFactory())
        )

        result = controller.open_document(document)
        result.window["on_action"](
            EditorAction(EditorActionType.PENDING_DISCARD, "Discard", "pending:pending-001")
        )

        groups = dict(result.window["navigator"])
        self.assertEqual("dashboard", result.window["selected_item_id"])
        self.assertNotIn("Pending", groups)
        self.assertEqual("success", controller.last_action_result.status)

    def test_open_session_editor_command_resolves_without_qt_or_pya(self) -> None:
        services = build_app_services()

        services.commands.dispatch(CommandId.OPEN_SESSION_EDITOR)

        self.assertIsNone(services.session_editor_controller.current_document)

    def test_process_aware_document_surfaces_attach_recipe_primary_action(self) -> None:
        document = SessionDocumentBuilder().build(empty_session())
        factory = InMemorySessionEditorWidgetFactory()

        window = SessionEditorShell(factory).open(
            document,
            DefaultSessionModeAdapter(),
            SessionEditorCallbacks(lambda _item_id: None, lambda _action: None),
        )

        self.assertIn("Attach Recipe", [action.label for action in window["primary_actions"]])
        self.assertNotIn("Add Capture", [action.label for action in window["primary_actions"]])
        self.assertIn(("Process Context", "none"), window["header"])
