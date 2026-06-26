import unittest
from dataclasses import replace

from metrology_process_planner.domains.geometry import Box
from metrology_process_planner.domains.session import (
    CanvasObject,
    CanvasObjectType,
    CanvasWorkflowState,
    CaptureGeometry,
    PendingCapture,
    SessionMode,
    SessionRecord,
)
from metrology_process_planner.persistence.csv_export import CaptureCsvExporter
from metrology_process_planner.workflows import InteractionContext
from metrology_process_planner.workflows.editor import (
    SessionDocumentBuilder,
    apply_metadata_edits,
    mark_metadata_edit,
)
from metrology_process_planner.workflows.pending_capture_review import PendingCaptureReviewService
from tests.editor_render_fixtures import session


class CadReviewMetadataValidationTests(unittest.TestCase):
    def test_cad_review_save_normalizes_invalid_review_metadata(self) -> None:
        source = _pending_session(
            metadata={"review_category": "Needs Triage", "severity": "urgent"},
        )

        result = PendingCaptureReviewService().save_pending_box(
            source,
            InteractionContext(),
            "pending-001",
            label="Review item",
        )

        capture = result.session.captures[0]
        self.assertEqual("other", capture.metadata["review_category"])
        self.assertEqual("medium", capture.metadata["severity"])

    def test_saved_cad_review_metadata_edits_normalize_review_values(self) -> None:
        source = replace(session(), mode=SessionMode.CAD_REVIEW)
        document = SessionDocumentBuilder().build(source)
        dirty = mark_metadata_edit(
            document,
            "capture:cap-001",
            "review_category",
            "process risk",
        )
        dirty = mark_metadata_edit(dirty, "capture:cap-001", "severity", "urgent")

        applied = apply_metadata_edits(dirty)
        capture = applied.session.captures[0]

        self.assertEqual("process_risk", capture.metadata["review_category"])
        self.assertEqual("medium", capture.metadata["severity"])

    def test_saved_cad_review_label_edit_updates_metadata_label(self) -> None:
        source = replace(session(), mode=SessionMode.CAD_REVIEW)
        document = SessionDocumentBuilder().build(source)
        dirty = mark_metadata_edit(
            document,
            "capture:cap-001",
            "label",
            "Reticle Alignment Question",
        )

        applied = apply_metadata_edits(dirty)
        capture = applied.session.captures[0]

        self.assertEqual("Reticle Alignment Question", capture.label)
        self.assertEqual("Reticle Alignment Question", capture.metadata["label"])

    def test_cad_review_csv_exports_review_metadata_columns(self) -> None:
        source = replace(session(), mode=SessionMode.CAD_REVIEW)
        document = SessionDocumentBuilder().build(source)
        dirty = mark_metadata_edit(
            document,
            "capture:cap-001",
            "review_category",
            "design_question",
        )
        dirty = mark_metadata_edit(dirty, "capture:cap-001", "severity", "high")
        dirty = mark_metadata_edit(dirty, "capture:cap-001", "owner", "layout-review")
        dirty = mark_metadata_edit(dirty, "capture:cap-001", "tags", "overlay;question")

        applied = apply_metadata_edits(dirty)
        row = CaptureCsvExporter().rows_for_session(applied.session)[0]

        self.assertEqual("design_question", row["review_category"])
        self.assertEqual("high", row["review_severity"])
        self.assertEqual("layout-review", row["review_owner"])
        self.assertEqual("overlay;question", row["tags"])


def _pending_session(metadata: dict[str, object]) -> SessionRecord:
    return SessionRecord(
        id="session-001",
        name="Demo",
        mode=SessionMode.CAD_REVIEW,
        created_at="2026-06-24T00:00:00Z",
        updated_at="2026-06-24T00:00:00Z",
        canvas_objects=(
            CanvasObject(
                "canvas-pending",
                "session-001",
                "pending-001",
                CanvasObjectType.SITE_BOX,
                None,
                CaptureGeometry.box(Box(0, 0, 5, 5)),
                CanvasWorkflowState.PENDING,
            ),
        ),
        pending_captures=(
            PendingCapture(
                "pending-001",
                "session-001",
                "canvas-pending",
                CanvasObjectType.SITE_BOX,
                CaptureGeometry.box(Box(0, 0, 5, 5)),
                metadata=metadata,
            ),
        ),
    )


if __name__ == "__main__":
    unittest.main()
