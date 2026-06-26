import unittest

from metrology_process_planner.domains.geometry import Point
from metrology_process_planner.domains.session import (
    CanvasObjectType,
    CanvasWorkflowState,
    SessionMode,
    SessionRecord,
)
from metrology_process_planner.ui.capture.tools import CaptureGesture, PointCaptureTool
from metrology_process_planner.workflows import InteractionContext, PendingCaptureReviewService


class StandalonePointCaptureTests(unittest.TestCase):
    def test_point_click_can_save_as_standalone_capture(self) -> None:
        tool = PointCaptureTool()
        context = tool.arm(InteractionContext())
        captured = tool.handle(_session(), context, CaptureGesture("click", Point(4, 7), True))

        saved = PendingCaptureReviewService().save_pending_box(
            captured.session,
            captured.context,
            "pending-001",
            label="Point 1",
        )

        capture = saved.session.captures[0]
        canvas_object = saved.session.canvas_objects[0]
        self.assertEqual((), saved.session.pending_captures)
        self.assertEqual("Point 1", capture.label)
        self.assertEqual("point", capture.geometry.kind.value)
        self.assertEqual(Point(4, 7), capture.geometry.point)
        self.assertEqual(CanvasObjectType.POINT, canvas_object.object_type)
        self.assertEqual(CanvasWorkflowState.SAVED, canvas_object.workflow_state)

    def test_point_capture_uses_next_pending_id_after_saved_capture(self) -> None:
        base = _session()
        first = PointCaptureTool().handle(
            base,
            PointCaptureTool().arm(InteractionContext()),
            CaptureGesture("click", Point(1, 1), True),
        )
        saved = PendingCaptureReviewService().save_pending_box(
            first.session,
            first.context,
            "pending-001",
        )

        second = PointCaptureTool().handle(
            saved.session,
            PointCaptureTool().arm(saved.context),
            CaptureGesture("click", Point(2, 2), True),
        )

        self.assertEqual("pending-002", second.session.pending_captures[0].id)


def _session() -> SessionRecord:
    return SessionRecord(
        id="session-001",
        name="Demo Session",
        mode=SessionMode.SIMPLE_CAPTURE,
        created_at="2026-06-25T00:00:00Z",
        updated_at="2026-06-25T00:00:00Z",
    )


if __name__ == "__main__":
    unittest.main()
