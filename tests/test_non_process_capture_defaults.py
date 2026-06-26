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


class NonProcessCaptureDefaultsTestsPart1(unittest.TestCase):
    def test_fast_batch_pending_save_uses_stable_auto_label_and_sequence(self) -> None:
        source = _pending_session(SessionMode.FAST_BATCH_CAPTURE)
        result = PendingCaptureReviewService().save_pending_box(
            source,
            InteractionContext(),
            "pending-001",
        )

        capture = result.session.captures[0]
        self.assertEqual(1, capture.sequence)
        self.assertEqual("Capture 001", capture.label)
        self.assertEqual("site", capture.role)
        self.assertEqual("layout_region", capture.type)

    def test_fast_batch_sequence_advances_after_existing_capture(self) -> None:
        source = _pending_session(
            SessionMode.FAST_BATCH_CAPTURE,
            captures=(
                CaptureRecord(
                    id="cap-007",
                    sequence=7,
                    label="Capture 007",
                    geometry=CaptureGeometry.box(Box(0, 0, 5, 5)),
                    created_at="2026-06-24T00:00:00Z",
                ),
            ),
        )
        result = PendingCaptureReviewService().save_pending_box(
            source,
            InteractionContext(),
            "pending-001",
        )

        capture = result.session.captures[-1]
        self.assertEqual("cap-008", capture.id)
        self.assertEqual(8, capture.sequence)
        self.assertEqual("Capture 008", capture.label)

    def test_simple_capture_save_preserves_optional_capture_type_metadata(self) -> None:
        source = _pending_session(
            SessionMode.SIMPLE_CAPTURE,
            metadata={"capture_type": "defect_region"},
        )

        result = PendingCaptureReviewService().save_pending_box(
            source,
            InteractionContext(),
            "pending-001",
            label="Defect A",
        )

        capture = result.session.captures[0]
        self.assertEqual("defect_region", capture.type)
        self.assertEqual("defect_region", capture.metadata["capture_type"])
        self.assertEqual("Defect A", capture.metadata["label"])
        self.assertEqual(capture.role, capture.metadata["capture_role"])

    def test_requested_label_overrides_stale_pending_label_metadata(self) -> None:
        source = _pending_session(
            SessionMode.SIMPLE_CAPTURE,
            metadata={"label": "Old Pending Label"},
        )

        result = PendingCaptureReviewService().save_pending_box(
            source,
            InteractionContext(),
            "pending-001",
            label="Operator Label",
        )

        capture = result.session.captures[0]
        self.assertEqual("Operator Label", capture.label)
        self.assertEqual("Operator Label", capture.metadata["label"])
