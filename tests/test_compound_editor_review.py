import unittest

from metrology_process_planner.domains.geometry import Point
from metrology_process_planner.domains.session import (
    CanvasWorkflowState,
    SessionMode,
)
from metrology_process_planner.ui.review import PendingCaptureReviewPresenter
from metrology_process_planner.workflows.compound_capture import (
    add_line_feature,
    add_point_feature,
    arm_inner_feature_capture,
    ellipsometry_request,
    profilometry_request,
)
from metrology_process_planner.workflows.editor import (
    DefaultSessionModeAdapter,
    EditorAction,
    EditorActionDispatcher,
    EditorActionType,
    SessionDocumentBuilder,
)
from tests.compound_capture_fixtures import pending_parent


class CompoundEditorReviewTests(unittest.TestCase):
    def test_pending_composite_exposes_review_actions_and_canvas_indexes(self) -> None:
        document = SessionDocumentBuilder().build(_pending_profile_document_session())
        item = document.items_by_id["pending:pending-001"]
        actions = DefaultSessionModeAdapter().actions(document.session, item)

        self.assertEqual(("canvas-parent", "canvas-001"), item.canvas_object_ids)
        self.assertIn("canvas-001", document.selection.selected_canvas_object_ids)
        self.assertIn(EditorActionType.COMPOSITE_SAVE, {action.action_type for action in actions})
        self.assertIn("Retake Line", [action.label for action in actions])
        self.assertIn("Retake Site Box", [action.label for action in actions])

    def test_presenter_uses_generic_composite_actions(self) -> None:
        document = SessionDocumentBuilder().build(_pending_point_document_session())

        view_model = PendingCaptureReviewPresenter().build_selected(document)

        self.assertIsNotNone(view_model)
        assert view_model is not None
        self.assertIn("composite_save", [action.action_id for action in view_model.actions])
        self.assertIn("Retake Point", [action.label for action in view_model.actions])
        self.assertIn("child_kind", [field.key for field in view_model.metadata_fields])

    def test_composite_save_promotes_capture_and_highlights_parent_and_child(self) -> None:
        document = SessionDocumentBuilder().build(_pending_profile_document_session())

        result = EditorActionDispatcher().dispatch(
            document,
            EditorAction(EditorActionType.COMPOSITE_SAVE, "Save Composite", "pending:pending-001"),
        )

        self.assertEqual("warning", result.status)
        self.assertEqual((), result.document.session.pending_captures)
        capture = result.document.session.captures[0]
        item = result.document.items_by_id[f"capture:{capture.id}"]
        self.assertEqual(("canvas-parent", "canvas-001"), item.canvas_object_ids)
        self.assertEqual(
            CanvasWorkflowState.SAVED,
            result.document.session.canvas_objects[0].workflow_state,
        )
        self.assertEqual(
            CanvasWorkflowState.SAVED,
            result.document.session.canvas_objects[1].workflow_state,
        )
        self.assertIn("feature:feat-001", result.document.items_by_id)

    def test_retake_inner_feature_keeps_parent_and_rearms_child(self) -> None:
        document = SessionDocumentBuilder().build(_pending_profile_document_session())

        result = EditorActionDispatcher().dispatch(
            document,
            EditorAction(
                EditorActionType.COMPOSITE_RETAKE_INNER,
                "Retake Line",
                "pending:pending-001",
            ),
        )

        session = result.document.session
        self.assertEqual(("canvas-parent",), tuple(item.id for item in session.canvas_objects))
        self.assertEqual("site_then_line:child", session.workflow.stage)
        self.assertEqual("measurement", session.workflow.active_primitive)
        self.assertNotIn("feature", dict(session.pending_captures[0].metadata)["compound"])

    def test_retake_parent_and_discard_remove_composite_overlays(self) -> None:
        document = SessionDocumentBuilder().build(_pending_profile_document_session())

        retake = EditorActionDispatcher().dispatch(
            document,
            EditorAction(
                EditorActionType.COMPOSITE_RETAKE_PARENT,
                "Retake Site Box",
                "pending:pending-001",
            ),
        )
        discard = EditorActionDispatcher().dispatch(
            document,
            EditorAction(
                EditorActionType.COMPOSITE_DISCARD,
                "Discard Composite",
                "pending:pending-001",
            ),
        )

        self.assertEqual((), retake.document.session.pending_captures)
        self.assertEqual((), retake.document.session.canvas_objects)
        self.assertEqual("site_then_line:parent", retake.document.session.workflow.stage)
        self.assertEqual("site_box", retake.document.session.workflow.active_primitive)
        self.assertEqual((), discard.document.session.pending_captures)
        self.assertEqual((), discard.document.session.canvas_objects)

    def test_exit_preserves_pending_composite_but_clears_armed_primitive(self) -> None:
        document = SessionDocumentBuilder().build(_pending_profile_document_session())

        result = EditorActionDispatcher().dispatch(
            document,
            EditorAction(EditorActionType.COMPOSITE_EXIT, "Exit", "pending:pending-001"),
        )

        self.assertEqual(1, len(result.document.session.pending_captures))
        self.assertEqual(2, len(result.document.session.canvas_objects))
        self.assertFalse(result.document.session.workflow.active)
        self.assertEqual("", result.document.session.workflow.active_primitive)


def _pending_profile_document_session():
    session = arm_inner_feature_capture(
        pending_parent(SessionMode.PROFILOMETRY_PLANNER),
        "pending-001",
        profilometry_request(),
    )
    return add_line_feature(
        session,
        "pending-001",
        Point(1, 1),
        Point(9, 9),
        profilometry_request(),
    )


def _pending_point_document_session():
    session = arm_inner_feature_capture(
        pending_parent(SessionMode.ELLIPSOMETRY_PLANNER),
        "pending-001",
        ellipsometry_request(),
    )
    return add_point_feature(session, "pending-001", Point(5, 5), ellipsometry_request())


if __name__ == "__main__":
    unittest.main()
