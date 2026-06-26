import unittest

from metrology_process_planner.domains.session import SessionMode, SessionRecord
from metrology_process_planner.ui.session_editor.header import header_entries, primary_actions
from metrology_process_planner.workflows.editor import SessionDocumentBuilder


class SessionEditorHeaderTests(unittest.TestCase):
    def test_setup_modes_surface_setup_header_and_primary_action(self) -> None:
        document = SessionDocumentBuilder().build(
            SessionRecord(
                id="session-001",
                name="Optical Demo",
                mode=SessionMode.OPTICAL_METROLOGY,
                created_at="2026-06-23T20:00:00Z",
                updated_at="2026-06-23T20:00:00Z",
            )
        )

        self.assertIn("Setup", [label for label, _value in header_entries(document)])
        self.assertIn("Reopen Setup", [action.label for action in primary_actions(document)])


if __name__ == "__main__":
    unittest.main()
