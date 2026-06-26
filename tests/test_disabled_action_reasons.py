import unittest

from metrology_process_planner.ui.review import PendingCaptureReviewPresenter
from metrology_process_planner.ui.session_editor.header import primary_actions
from metrology_process_planner.workflows.editor import (
    DefaultSessionModeAdapter,
    EditorAction,
    EditorActionDispatcher,
    EditorActionType,
    SessionDocumentBuilder,
)
from tests.editor_render_fixtures import session


class DisabledActionReasonTests(unittest.TestCase):
    def test_header_build_report_is_enabled(self) -> None:
        document = SessionDocumentBuilder().build(session())

        actions = {action.label: action for action in primary_actions(document)}

        self.assertTrue(actions["Build Report"].enabled)
        self.assertEqual("", actions["Build Report"].disabled_reason)

    def test_adapter_exports_enabled_report_action(self) -> None:
        document = SessionDocumentBuilder().build(session())
        item = document.items_by_id[document.selection.selected_item_id]

        actions = DefaultSessionModeAdapter().actions(document.session, item)
        report = next(action for action in actions if action.label == "Build Report")

        self.assertTrue(report.enabled)
        self.assertEqual("", report.disabled_reason)

    def test_pending_review_preserves_enabled_report_action(self) -> None:
        document = SessionDocumentBuilder().build(session())

        review = PendingCaptureReviewPresenter().build_selected(document)
        report = next(action for action in review.actions if action.label == "Build Report")

        self.assertTrue(report.enabled)
        self.assertEqual("available", report.status)
        self.assertEqual("", report.disabled_reason)

    def test_dispatcher_returns_reason_for_disabled_action(self) -> None:
        document = SessionDocumentBuilder().build(session())
        action = EditorAction(
            EditorActionType.BUILD_POWERPOINT,
            "Build Report",
            enabled=False,
            disabled_reason="Report generation is not wired yet.",
        )

        result = EditorActionDispatcher().dispatch(document, action)

        self.assertEqual("unavailable", result.status)
        self.assertEqual("Report generation is not wired yet.", result.message)


if __name__ == "__main__":
    unittest.main()
