import unittest
from dataclasses import replace

from metrology_process_planner.app.session_editor import SessionEditorController
from metrology_process_planner.domains.session import WarningRecord
from metrology_process_planner.ui.session_editor import InMemorySessionEditorWidgetFactory
from metrology_process_planner.ui.session_editor.navigator import (
    NavigatorFilterState,
    navigator_groups,
)
from metrology_process_planner.ui.session_editor.shell import SessionEditorShell
from metrology_process_planner.workflows.editor import SessionDocumentBuilder
from tests.editor_render_fixtures import session


class SessionEditorNavigatorTests(unittest.TestCase):
    def test_navigator_search_preserves_non_empty_groups(self) -> None:
        document = SessionDocumentBuilder().build(session())

        groups = dict(navigator_groups(document, NavigatorFilterState("Site")))

        self.assertEqual((("capture:cap-001", "Site 1"),), groups["Saved Captures"])
        self.assertNotIn("Dashboard", groups)

    def test_warning_filter_keeps_only_warning_items(self) -> None:
        document = SessionDocumentBuilder().build(_session_with_error_warning())

        groups = dict(navigator_groups(document, NavigatorFilterState("", "warnings_only")))

        self.assertEqual((("warning:warn-error", "Recipe failed"),), groups["Warnings"])
        self.assertNotIn("Saved Captures", groups)

    def test_controller_filter_callback_rerenders_navigator(self) -> None:
        document = SessionDocumentBuilder().build(session())
        controller = SessionEditorController(
            shell=SessionEditorShell(InMemorySessionEditorWidgetFactory())
        )

        result = controller.open_document(document)
        result.window["on_filter_navigator"]("Site", "all")

        groups = dict(result.window["navigator"])
        self.assertEqual((("capture:cap-001", "Site 1"),), groups["Saved Captures"])
        self.assertEqual("Site", result.window["navigator_filter"].query)


def _session_with_error_warning():
    warning = WarningRecord("warn-error", "Recipe failed", severity="error")
    return replace(session(), warnings=(warning,))


if __name__ == "__main__":
    unittest.main()
