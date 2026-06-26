import unittest
from dataclasses import replace

from metrology_process_planner.domains.session import SessionMode
from metrology_process_planner.persistence.csv_export import CaptureCsvExporter
from metrology_process_planner.workflows.editor import (
    EditorAction,
    EditorActionDispatcher,
    EditorActionType,
    SessionDocumentBuilder,
    apply_metadata_edits,
    mark_metadata_edit,
)
from tests.editor_render_fixtures import session


class NonProcessMetadataFieldTestsPart2(unittest.TestCase):
    def test_saved_capture_role_and_type_edits_update_canonical_fields(self) -> None:
        source = session()
        document = SessionDocumentBuilder().build(source)
        dirty = mark_metadata_edit(document, "capture:cap-001", "capture_role", "metrology_site")
        dirty = mark_metadata_edit(dirty, "capture:cap-001", "capture_type", "alignment_region")

        applied = apply_metadata_edits(dirty)
        capture = applied.session.captures[0]

        self.assertEqual("metrology_site", capture.role)
        self.assertEqual("alignment_region", capture.type)
        self.assertEqual("metrology_site", capture.metadata["capture_role"])
        self.assertEqual("alignment_region", capture.metadata["capture_type"])

    def test_saved_capture_tag_edits_round_trip_as_structured_metadata(self) -> None:
        source = replace(session(), mode=SessionMode.CAD_REVIEW)
        document = SessionDocumentBuilder().build(source)
        dirty = mark_metadata_edit(
            document,
            "capture:cap-001",
            "tags",
            "overlay, alignment; review",
        )

        applied = apply_metadata_edits(dirty)
        capture = applied.session.captures[0]
        rows = CaptureCsvExporter().rows_for_session(applied.session)

        self.assertEqual(("overlay", "alignment", "review"), capture.metadata["tags"])
        self.assertEqual("overlay;alignment;review", rows[0]["tags"])

    def test_saved_cad_review_metadata_edits_normalize_review_values(self) -> None:
        source = replace(session(), mode=SessionMode.CAD_REVIEW)
        document = SessionDocumentBuilder().build(source)
        dirty = mark_metadata_edit(document, "capture:cap-001", "review_category", "process risk")
        dirty = mark_metadata_edit(dirty, "capture:cap-001", "severity", "urgent")

        applied = apply_metadata_edits(dirty)
        capture = applied.session.captures[0]

        self.assertEqual("process_risk", capture.metadata["review_category"])
        self.assertEqual("medium", capture.metadata["severity"])

    def test_pending_capture_tag_edits_are_saved_as_structured_metadata(self) -> None:
        source = replace(session(), mode=SessionMode.CAD_REVIEW)
        document = SessionDocumentBuilder().build(source)
        dirty = mark_metadata_edit(document, "pending:pending-001", "tags", "overlay, alignment")

        applied = apply_metadata_edits(dirty)
        result = EditorActionDispatcher().dispatch(
            applied,
            EditorAction(EditorActionType.PENDING_SAVE, "Save", "pending:pending-001"),
        )
        capture = result.document.session.captures[-1]

        self.assertEqual(("overlay", "alignment"), capture.metadata["tags"])

    def test_cdsem_pending_save_persists_default_feature_type(self) -> None:
        source = replace(session(), mode=SessionMode.CDSEM_MEASUREMENT)
        document = SessionDocumentBuilder().build(source)

        result = EditorActionDispatcher().dispatch(
            document,
            EditorAction(EditorActionType.PENDING_SAVE, "Save", "pending:pending-001"),
        )
        capture = result.document.session.captures[-1]

        self.assertEqual("line", capture.metadata["feature_type"])


if __name__ == "__main__":
    unittest.main()
