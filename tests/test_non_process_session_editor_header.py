import unittest
from dataclasses import replace

from metrology_process_planner.domains.session import ProcessContext
from metrology_process_planner.ui.session_editor import (
    InMemorySessionEditorWidgetFactory,
    SessionEditorCallbacks,
    SessionEditorShell,
)
from metrology_process_planner.workflows.editor import (
    DefaultSessionModeAdapter,
    SessionDocumentBuilder,
)
from tests.editor_render_fixtures import session


class NonProcessSessionEditorHeaderTests(unittest.TestCase):
    def test_header_hides_process_actions_even_with_attached_context(self) -> None:
        source = replace(session(), process_context=ProcessContext(recipe_id="legacy-recipe"))

        window = SessionEditorShell(InMemorySessionEditorWidgetFactory()).open(
            SessionDocumentBuilder().build(source),
            DefaultSessionModeAdapter(),
            SessionEditorCallbacks(lambda _item_id: None, lambda _action: None),
        )

        labels = [action.label for action in window["primary_actions"]]
        self.assertNotIn("Validate Process Context", labels)
        self.assertNotIn("Attach Recipe", labels)
        self.assertNotIn("Process Context", [label for label, _value in window["header"]])


if __name__ == "__main__":
    unittest.main()
