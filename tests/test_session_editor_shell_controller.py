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
from tests.editor_render_fixtures import session as rich_session


class SessionEditorShellControllerTests(unittest.TestCase):
    def test_shell_renders_generic_sections_and_callbacks(self) -> None:
        selected: list[str] = []
        actions: list[EditorAction] = []
        document = _document()
        factory = InMemorySessionEditorWidgetFactory()

        window = SessionEditorShell(factory).open(
            document,
            DefaultSessionModeAdapter(),
            SessionEditorCallbacks(selected.append, actions.append),
        )
        window["on_select"]("dashboard")
        window["on_action"](EditorAction(EditorActionType.SAVE_EDITS, "Save"))

        self.assertTrue(window["shown"])
        self.assertIn(("Session", "Demo"), window["header"])
        self.assertTrue(window["navigator"])
        self.assertTrue(window["preview"])
        self.assertTrue(window["fields"])
        self.assertEqual(["dashboard"], selected)
        self.assertEqual(EditorActionType.SAVE_EDITS, actions[0].action_type)

    def test_controller_opens_document_and_routes_action_callback(self) -> None:
        document = _document()
        controller = SessionEditorController(
            shell=SessionEditorShell(InMemorySessionEditorWidgetFactory())
        )

        result = controller.open_document(document)
        result.window["on_action"](EditorAction(EditorActionType.BUILD_POWERPOINT, "Build"))

        self.assertEqual("opened", result.status)
        self.assertEqual("unavailable", controller.last_action_result.status)

    def test_controller_rerenders_shell_after_selection_callback(self) -> None:
        document = SessionDocumentBuilder().build(rich_session())
        controller = SessionEditorController(
            shell=SessionEditorShell(InMemorySessionEditorWidgetFactory())
        )

        result = controller.open_document(document)
        result.window["on_select"]("capture:cap-001")

        self.assertEqual("capture:cap-001", controller.current_document.selection.selected_item_id)
        self.assertEqual("capture:cap-001", result.window["selected_item_id"])
        self.assertIn(("label", "Label", "Site 1"), result.window["fields"])
        self.assertTrue(
            any(
                action.action_type is EditorActionType.ADD_MEASUREMENT
                for action in result.window["actions"]
            )
        )

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
