import unittest
from dataclasses import replace

from metrology_process_planner.app.session_editor_command_map import command_for_action
from metrology_process_planner.domains.session import (
    SessionMode,
    SessionModeId,
    SessionRecord,
    SetupItemRecord,
    SetupState,
)
from metrology_process_planner.ui.session_editor.header import primary_actions
from metrology_process_planner.workflows.editor import (
    DefaultSessionModeAdapter,
    EditorAction,
    EditorActionType,
    SessionDocumentBuilder,
)
from tests.editor_render_fixtures import empty_session, session


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


class SessionEditorCapturePrimaryActionTestsPart2(unittest.TestCase):
    def test_recipe_free_header_primary_actions_are_routable(self) -> None:
        modes = (
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

        documents = [
            _document(mode)
            for mode in modes
        ]
        documents.append(SessionDocumentBuilder().build(session()))

        for document in documents:
            with self.subTest(mode=document.session.mode.value):
                for action in primary_actions(document, DefaultSessionModeAdapter()):
                    self.assertTrue(
                        command_for_action(action) is not None
                        or action.action_type is EditorActionType.SELECT_ITEM,
                        f"{action.action_type.value} has no app command or editor route",
                    )

    def test_setup_blocked_modes_keep_add_capture_visible_with_reason(self) -> None:
        modes = (
            (
                SessionMode.OPTICAL_METROLOGY,
                "Complete required setup before capture: Optical Alignment Mark.",
            ),
            (
                SessionMode.CDSEM_MEASUREMENT,
                "Complete required setup before capture: "
                "Optical Alignment Mark, SEM Alignment Mark.",
            ),
        )

        for mode, reason in modes:
            with self.subTest(mode=mode.value):
                document = _document(mode)
                action = next(
                    item
                    for item in primary_actions(document, DefaultSessionModeAdapter())
                    if item.action_type is EditorActionType.ADD_CAPTURE
                )

                self.assertEqual("Add Capture", action.label)
                self.assertFalse(action.enabled)
                self.assertEqual(reason, action.disabled_reason)

    def test_setup_ready_modes_enable_add_capture_header_action(self) -> None:
        source = replace(
            empty_session(),
            mode=SessionMode.CDSEM_MEASUREMENT,
            setup=SetupState(
                items=(
                    _complete_setup_item("optical_alignment", "Optical Alignment Mark"),
                    _complete_setup_item("sem_alignment", "SEM Alignment Mark"),
                ),
                is_capture_ready=True,
            ),
        )
        document = SessionDocumentBuilder().build(source)

        action = next(
            item
            for item in primary_actions(document, DefaultSessionModeAdapter())
            if item.action_type is EditorActionType.ADD_CAPTURE
        )

        self.assertTrue(action.enabled)
        self.assertEqual("", action.disabled_reason)
