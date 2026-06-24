import unittest

from metrology_process_planner.domains.geometry import Point
from metrology_process_planner.domains.session import SessionMode
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


class CompoundFeatureEditorItemTests(unittest.TestCase):
    def test_saved_line_feature_item_selects_only_child_canvas_object(self) -> None:
        saved = _save_pending(_pending_profile_session())

        selected = EditorActionDispatcher().dispatch(
            saved,
            EditorAction(EditorActionType.SELECT_ITEM, "Select Feature", "feature:feat-001"),
        )

        self.assertEqual(("canvas-001",), selected.document.selection.selected_canvas_object_ids)
        self.assertEqual(
            "feature:feat-001",
            selected.document.canvas_object_to_item_id["canvas-001"],
        )
        self.assertIn("length", _field_keys(selected.document, "feature:feat-001"))

    def test_saved_point_feature_item_selects_only_child_canvas_object(self) -> None:
        saved = _save_pending(_pending_point_session())

        selected = EditorActionDispatcher().dispatch(
            saved,
            EditorAction(EditorActionType.SELECT_ITEM, "Select Feature", "feature:feat-001"),
        )

        self.assertEqual(("canvas-001",), selected.document.selection.selected_canvas_object_ids)
        self.assertIn("x", _field_keys(selected.document, "feature:feat-001"))

    def test_saved_profile_capture_exposes_clean_composite_actions(self) -> None:
        document = _save_pending(_pending_profile_session())

        labels = _action_labels(document, "capture:cap-001")

        self.assertIn("Replace Site Box", labels)
        self.assertIn("Replace Line", labels)
        self.assertIn("Regenerate Line Annotation", labels)
        self.assertIn("Regenerate Process Output", labels)
        self.assertIn("Add Measurement", labels)

    def test_saved_point_capture_exposes_clean_composite_actions(self) -> None:
        document = _save_pending(_pending_point_session())

        labels = _action_labels(document, "capture:cap-001")

        self.assertIn("Replace Site Box", labels)
        self.assertIn("Replace Point", labels)
        self.assertIn("Regenerate Point Annotation", labels)
        self.assertIn("Regenerate Point Stack", labels)

    def test_replace_command_is_explicitly_unavailable_until_workflow_is_wired(self) -> None:
        document = _save_pending(_pending_profile_session())

        result = EditorActionDispatcher().dispatch(
            document,
            EditorAction(
                EditorActionType.REPLACE_INNER_FEATURE,
                "Replace Line",
                "capture:cap-001",
            ),
        )

        self.assertEqual("unavailable", result.status)
        self.assertIn("Replace Line", result.message)


def _save_pending(session):
    return EditorActionDispatcher().dispatch(
        SessionDocumentBuilder().build(session),
        EditorAction(EditorActionType.COMPOSITE_SAVE, "Save Composite", "pending:pending-001"),
    ).document


def _field_keys(document, item_id: str) -> list[str]:
    fields = DefaultSessionModeAdapter().metadata_fields(
        document.session,
        document.items_by_id[item_id],
    )
    return [field.key for field in fields]


def _action_labels(document, item_id: str) -> set[str]:
    actions = DefaultSessionModeAdapter().actions(
        document.session,
        document.items_by_id[item_id],
    )
    return {action.label for action in actions}


def _pending_profile_session():
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


def _pending_point_session():
    session = arm_inner_feature_capture(
        pending_parent(SessionMode.ELLIPSOMETRY_PLANNER),
        "pending-001",
        ellipsometry_request(),
    )
    return add_point_feature(session, "pending-001", Point(5, 5), ellipsometry_request())


if __name__ == "__main__":
    unittest.main()
