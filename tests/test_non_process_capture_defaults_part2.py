import unittest

from metrology_process_planner.domains.geometry import Box
from metrology_process_planner.domains.session import (
    CanvasObject,
    CanvasObjectType,
    CanvasWorkflowState,
    CaptureGeometry,
    CaptureRecord,
    PendingCapture,
    SessionMode,
    SessionRecord,
)
from metrology_process_planner.workflows import InteractionContext
from metrology_process_planner.workflows.editor import (
    DefaultSessionModeAdapter,
    SessionDocumentBuilder,
)
from metrology_process_planner.workflows.pending_capture_review import PendingCaptureReviewService


def _pending_session(
    mode: SessionMode,
    metadata: dict[str, object] | None = None,
    captures: tuple[CaptureRecord, ...] = (),
) -> SessionRecord:
    return SessionRecord(
        id="session-001",
        name="Demo",
        mode=mode,
        created_at="2026-06-24T00:00:00Z",
        updated_at="2026-06-24T00:00:00Z",
        captures=captures,
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
                metadata=metadata or {},
            ),
        ),
    )


class NonProcessCaptureDefaultsTestsPart2(unittest.TestCase):
    def test_cad_review_metadata_is_visible_and_saved_without_process_context(self) -> None:
        source = _pending_session(
            SessionMode.CAD_REVIEW,
            metadata={
                "review_category": "alignment",
                "severity": "medium",
                "owner": "process-review",
                "tags": ("overlay", "alignment"),
            },
        )
        document = SessionDocumentBuilder().build(source)
        adapter = DefaultSessionModeAdapter()

        pending_fields = adapter.metadata_fields(
            source,
            document.items_by_id["pending:pending-001"],
        )
        result = PendingCaptureReviewService().save_pending_box(
            source,
            InteractionContext(),
            "pending-001",
            label="Overlay check",
            notes="Inspect marker.",
        )

        capture = result.session.captures[0]
        self.assertIn("review_category", {field.key for field in pending_fields})
        self.assertIn("owner", {field.key for field in pending_fields})
        self.assertEqual("alignment", capture.metadata["review_category"])
        self.assertEqual("medium", capture.metadata["severity"])
        self.assertEqual("process-review", capture.metadata["owner"])
        self.assertEqual(("overlay", "alignment"), capture.metadata["tags"])
        self.assertEqual("review_region", capture.role)
        self.assertEqual("cad_review_region", capture.type)
        self.assertEqual("Overlay check", capture.metadata["label"])
        self.assertEqual("review_region", capture.metadata["capture_role"])
        self.assertEqual("cad_review_region", capture.metadata["capture_type"])

    def test_cad_review_save_uses_suggested_category_default(self) -> None:
        source = _pending_session(SessionMode.CAD_REVIEW)
        result = PendingCaptureReviewService().save_pending_box(
            source,
            InteractionContext(),
            "pending-001",
            label="Review item",
        )

        capture = result.session.captures[0]
        self.assertEqual("layout_issue", capture.metadata["review_category"])
        self.assertEqual("medium", capture.metadata["severity"])

    def test_cad_review_capture_alias_uses_cad_defaults(self) -> None:
        source = _pending_session(SessionMode.CAD_REVIEW_CAPTURE)

        result = PendingCaptureReviewService().save_pending_box(
            source,
            InteractionContext(),
            "pending-001",
            label="Review item",
        )

        capture = result.session.captures[0]
        self.assertEqual("layout_issue", capture.metadata["review_category"])
        self.assertEqual("medium", capture.metadata["severity"])
        self.assertEqual("review_region", capture.role)
        self.assertEqual("cad_review_region", capture.type)
