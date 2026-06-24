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
    mark_metadata_edit,
)
from tests.compound_capture_fixtures import pending_parent


class CompoundModeMetadataFieldTests(unittest.TestCase):
    def test_pending_profile_review_uses_mode_declared_fields(self) -> None:
        document = SessionDocumentBuilder().build(_pending_profile_session())

        keys = _field_keys(document, "pending:pending-001")

        self.assertIn("line_label", keys)
        self.assertIn("line_color", keys)
        self.assertIn("line_weight_px", keys)
        self.assertIn("text_scale", keys)
        self.assertIn("target", keys)
        self.assertIn("lsl", keys)
        self.assertIn("usl", keys)

    def test_pending_point_review_uses_mode_declared_fields(self) -> None:
        document = SessionDocumentBuilder().build(_pending_point_session())

        keys = _field_keys(document, "pending:pending-001")

        self.assertIn("point_label", keys)
        self.assertIn("film_target", keys)

    def test_reviewed_mode_metadata_is_saved_on_composite_capture(self) -> None:
        document = SessionDocumentBuilder().build(_pending_profile_session())
        document = mark_metadata_edit(document, "pending:pending-001", "line_label", "Gate Cut")

        result = EditorActionDispatcher().dispatch(
            document,
            EditorAction(EditorActionType.COMPOSITE_SAVE, "Save Composite", "pending:pending-001"),
        )

        self.assertEqual("Gate Cut", result.document.session.captures[0].metadata["line_label"])


def _field_keys(document, item_id: str) -> set[str]:
    fields = DefaultSessionModeAdapter().metadata_fields(
        document.session,
        document.items_by_id[item_id],
    )
    return {field.key for field in fields}


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
