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
    def test_header_build_report_is_disabled_with_reason(self) -> None:
        document = SessionDocumentBuilder().build(session())

        actions = {action.label: action for action in primary_actions(document)}

        self.assertFalse(actions["Build Report"].enabled)
        self.assertEqual(
            "Report generation is not wired yet.",
            actions["Build Report"].disabled_reason,
        )

    def test_adapter_exports_disabled_report_action_reason(self) -> None:
        document = SessionDocumentBuilder().build(session())
        item = document.items_by_id[document.selection.selected_item_id]

        actions = DefaultSessionModeAdapter().actions(document.session, item)
        report = next(action for action in actions if action.label == "Build PowerPoint")

        self.assertFalse(report.enabled)
        self.assertEqual(
            "PowerPoint report generation is not wired yet.",
            report.disabled_reason,
        )

    def test_pending_review_preserves_disabled_reason_in_button_model(self) -> None:
        document = SessionDocumentBuilder().build(session())

        review = PendingCaptureReviewPresenter().build_selected(document)
        report = next(action for action in review.actions if action.label == "Build PowerPoint")

        self.assertFalse(report.enabled)
        self.assertEqual("disabled", report.status)
        self.assertEqual(
            "PowerPoint report generation is not wired yet.",
            report.disabled_reason,
        )

    def test_dispatcher_returns_reason_for_disabled_action(self) -> None:
        document = SessionDocumentBuilder().build(session())
        action = EditorAction(
            EditorActionType.BUILD_POWERPOINT,
            "Build PowerPoint",
            enabled=False,
            disabled_reason="Report generation is not wired yet.",
        )

        result = EditorActionDispatcher().dispatch(document, action)

        self.assertEqual("unavailable", result.status)
        self.assertEqual("Report generation is not wired yet.", result.message)


if __name__ == "__main__":
    unittest.main()
