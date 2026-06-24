import unittest
from dataclasses import replace

from metrology_process_planner.domains.geometry import Point
from metrology_process_planner.domains.session import SessionMode
from metrology_process_planner.workflows.compound_capture import (
    SaveCompositeCaptureCommand,
    add_line_feature,
    add_point_feature,
    arm_inner_feature_capture,
    ellipsometry_request,
    profilometry_request,
    save_composite_capture,
)
from metrology_process_planner.workflows.editor import (
    EditorAction,
    EditorActionDispatcher,
    EditorActionType,
    SessionDocumentBuilder,
    mark_metadata_edit,
)
from tests.compound_capture_fixtures import pending_parent


class CompoundSaveValidationTests(unittest.TestCase):
    def test_invalid_reviewed_specs_return_warning_without_saving(self) -> None:
        document = SessionDocumentBuilder().build(_profile_session())
        document = mark_metadata_edit(document, "pending:pending-001", "target", "5")
        document = mark_metadata_edit(document, "pending:pending-001", "lsl", "7")
        document = mark_metadata_edit(document, "pending:pending-001", "usl", "10")

        result = EditorActionDispatcher().dispatch(
            document,
            EditorAction(EditorActionType.COMPOSITE_SAVE, "Save Composite", "pending:pending-001"),
        )

        self.assertEqual("warning", result.status)
        self.assertIn("LSL <= target <= USL", result.message)
        self.assertEqual((), result.document.session.captures)
        self.assertEqual(1, len(result.document.session.pending_captures))
        self.assertEqual(2, len(result.document.session.canvas_objects))

    def test_invalid_line_annotation_settings_return_warning(self) -> None:
        document = SessionDocumentBuilder().build(_profile_session())
        document = mark_metadata_edit(document, "pending:pending-001", "line_color", "cyan")
        document = mark_metadata_edit(document, "pending:pending-001", "line_weight_px", "0")
        document = mark_metadata_edit(document, "pending:pending-001", "text_scale", "-1")

        result = EditorActionDispatcher().dispatch(
            document,
            EditorAction(EditorActionType.COMPOSITE_SAVE, "Save Composite", "pending:pending-001"),
        )

        self.assertEqual("warning", result.status)
        self.assertIn("Line color", result.message)
        self.assertIn("Line weight", result.message)
        self.assertIn("Text scale", result.message)
        self.assertEqual((), result.document.session.captures)

    def test_mode_policy_mismatch_is_rejected_before_save(self) -> None:
        session = _profile_session()
        pending = session.pending_captures[0]
        compound = dict(pending.metadata["compound"])
        compound["sequence_type"] = "site_then_point"
        session = replace(
            session,
            pending_captures=(replace(pending, metadata={"compound": compound}),),
        )

        with self.assertRaisesRegex(ValueError, "requires a point child feature"):
            save_composite_capture(session, SaveCompositeCaptureCommand("pending-001"))

    def test_feature_kind_and_role_are_revalidated_at_save(self) -> None:
        session = _point_session()
        pending = session.pending_captures[0]
        compound = dict(pending.metadata["compound"])
        feature = dict(compound["feature"])
        feature["role"] = "profilometry_line"
        compound["feature"] = feature
        session = replace(
            session,
            pending_captures=(replace(pending, metadata={"compound": compound}),),
        )

        with self.assertRaisesRegex(ValueError, "ellipsometry_point"):
            save_composite_capture(session, SaveCompositeCaptureCommand("pending-001"))


def _profile_session():
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


def _point_session():
    session = arm_inner_feature_capture(
        pending_parent(SessionMode.ELLIPSOMETRY_PLANNER),
        "pending-001",
        ellipsometry_request(),
    )
    return add_point_feature(session, "pending-001", Point(5, 5), ellipsometry_request())


if __name__ == "__main__":
    unittest.main()
