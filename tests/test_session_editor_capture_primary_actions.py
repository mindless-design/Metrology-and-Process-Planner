import unittest
from dataclasses import replace

from metrology_process_planner.app.bootstrap import build_app_services
from metrology_process_planner.app.commands import CommandId
from metrology_process_planner.domains.session import (
    SessionMode,
    SessionModeId,
    SessionRecord,
    SetupItemRecord,
)
from metrology_process_planner.ui.session_editor import (
    InMemorySessionEditorWidgetFactory,
    SessionEditorCallbacks,
    SessionEditorShell,
)
from metrology_process_planner.ui.session_editor.header import status_text
from metrology_process_planner.workflows.editor import (
    DefaultSessionModeAdapter,
    EditorAction,
    EditorActionType,
    SessionDocumentBuilder,
)
from tests.editor_render_fixtures import empty_session


def _primary_action(window, action_type: EditorActionType) -> EditorAction:
    return next(action for action in window["primary_actions"] if action.action_type is action_type)

def _primary_labels(window) -> list[str]:
    return [action.label for action in window["primary_actions"]]

def _document(mode: SessionMode | SessionModeId = SessionMode.SIMPLE_CAPTURE):
    session = replace(empty_session(), mode=mode)
    return SessionDocumentBuilder().build(session)

def _armed_document(session: SessionRecord):
    active = session.workflow.__class__(
        active=True,
        stage="box_capture",
        active_mode=session.mode.value,
        active_primitive="site_box",
        pending_item_ref="capture:box_capture",
    )
    return SessionDocumentBuilder().build(replace(session, workflow=active))

def _complete_setup_item(item_id: str, label: str) -> SetupItemRecord:
    return SetupItemRecord(
        item_id,
        "alignment_box_capture",
        label,
        "complete",
        metadata={"required": True},
    )

if __name__ == "__main__":
    unittest.main()


class SessionEditorCapturePrimaryActionTestsPart1(unittest.TestCase):
    def test_cancel_capture_primary_action_routes_to_shared_capture_command(self) -> None:
        services = build_app_services()
        document = SessionDocumentBuilder().build(
            replace(empty_session(), mode=SessionMode.SIMPLE_CAPTURE)
        )
        result = services.session_editor_controller.open_document(document)
        result.window["on_primary_action"](
            _primary_action(result.window, EditorActionType.ADD_CAPTURE)
        )

        action = _primary_action(result.window, EditorActionType.CANCEL_CAPTURE)
        result.window["on_primary_action"](action)

        routed = services.session_editor_controller.last_command_result
        current = services.session_editor_controller.current_document
        self.assertIsNotNone(routed)
        self.assertEqual(CommandId.CANCEL_CAPTURE, routed.command_id)
        self.assertEqual("success", routed.status)
        self.assertIsNotNone(current)
        self.assertFalse(current.session.workflow.active)
        self.assertEqual("", current.session.workflow.stage)

    def test_header_exposes_cancel_capture_only_while_capture_is_armed(self) -> None:
        document = _document()
        shell = SessionEditorShell(InMemorySessionEditorWidgetFactory())
        callbacks = SessionEditorCallbacks(lambda _item_id: None, lambda _action: None)

        window = shell.open(document, DefaultSessionModeAdapter(), callbacks)
        self.assertNotIn("Cancel Capture", _primary_labels(window))

        shell.render(
            window,
            _armed_document(document.session),
            DefaultSessionModeAdapter(),
            callbacks,
        )

        self.assertIn("Cancel Capture", _primary_labels(window))
        self.assertNotIn("Add Capture", _primary_labels(window))

    def test_fast_batch_header_uses_batch_capture_language(self) -> None:
        document = _document(SessionMode.FAST_BATCH_CAPTURE)
        shell = SessionEditorShell(InMemorySessionEditorWidgetFactory())
        callbacks = SessionEditorCallbacks(lambda _item_id: None, lambda _action: None)

        window = shell.open(document, DefaultSessionModeAdapter(), callbacks)

        self.assertIn("Start Batch Capture", _primary_labels(window))
        self.assertNotIn("Add Capture", _primary_labels(window))
        action = _primary_action(window, EditorActionType.ADD_CAPTURE)
        self.assertEqual("Start Batch Capture", action.label)

    def test_fast_batch_header_accepts_open_mode_id(self) -> None:
        document = _document(SessionModeId("fast_batch_capture"))
        shell = SessionEditorShell(InMemorySessionEditorWidgetFactory())
        callbacks = SessionEditorCallbacks(lambda _item_id: None, lambda _action: None)

        window = shell.open(document, DefaultSessionModeAdapter(), callbacks)

        self.assertIn("Start Batch Capture", _primary_labels(window))
        self.assertNotIn("Add Capture", _primary_labels(window))

    def test_fast_batch_active_header_exposes_exit_without_new_start(self) -> None:
        document = _document(SessionMode.FAST_BATCH_CAPTURE)
        shell = SessionEditorShell(InMemorySessionEditorWidgetFactory())
        callbacks = SessionEditorCallbacks(lambda _item_id: None, lambda _action: None)

        window = shell.open(document, DefaultSessionModeAdapter(), callbacks)
        shell.render(
            window,
            _armed_document(document.session),
            DefaultSessionModeAdapter(),
            callbacks,
        )

        labels = _primary_labels(window)
        self.assertIn("Exit Batch Capture", labels)
        self.assertNotIn("Start Batch Capture", labels)
        action = _primary_action(window, EditorActionType.CANCEL_CAPTURE)
        self.assertEqual("Exit Batch Capture", action.label)

    def test_fast_batch_status_text_explains_auto_save_and_exit(self) -> None:
        document = _armed_document(_document(SessionMode.FAST_BATCH_CAPTURE).session)

        status = status_text(document)

        self.assertIn("Fast Batch Capture active", status)
        self.assertIn("captures auto-save", status)
        self.assertIn("Exit Batch Capture", status)
