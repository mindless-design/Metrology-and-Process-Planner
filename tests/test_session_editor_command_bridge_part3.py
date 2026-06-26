import unittest

from metrology_process_planner.workflows.editor import (
    EditorAction,
    EditorActionDispatcher,
    EditorActionType,
    SessionDocumentBuilder,
    select_item,
)
from tests.editor_render_fixtures import session_without_pending


def _primary_action(window, action_type: EditorActionType) -> EditorAction:
    return next(action for action in window["primary_actions"] if action.action_type is action_type)

def _inspector_action(window, action_type: EditorActionType) -> EditorAction:
    return next(action for action in window["actions"] if action.action_type is action_type)

if __name__ == "__main__":
    unittest.main()


class SessionEditorCommandBridgeTestsPart3(unittest.TestCase):
    def test_inline_metadata_update_rejects_read_only_fields(self) -> None:
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
                payload=(("field_key", "center"), ("value", "0,0")),
            ),
        )

        self.assertEqual("unavailable", result.status)
        self.assertIn("read-only", result.message)
