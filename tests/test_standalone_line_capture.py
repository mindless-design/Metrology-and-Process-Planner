import unittest

from metrology_process_planner.domains.geometry import Point
from metrology_process_planner.domains.session import (
    CanvasObjectType,
    CanvasWorkflowState,
    SessionMode,
    SessionRecord,
)
from metrology_process_planner.ui.capture.tools import CaptureGesture, LineCaptureTool
from metrology_process_planner.workflows import InteractionContext, PendingCaptureReviewService


class StandaloneLineCaptureTests(unittest.TestCase):
    def test_line_drag_can_save_as_standalone_capture(self) -> None:
        tool = LineCaptureTool()
        context = tool.arm(InteractionContext())
        started = tool.handle(_session(), context, CaptureGesture("drag_start", Point(1, 1), True))
        updated = tool.handle(
            started.session,
            started.context,
            CaptureGesture("drag_update", Point(3, 1), True),
        )
        captured = tool.handle(
            updated.session,
            updated.context,
            CaptureGesture("drag_release", Point(4, 1), True),
        )

        saved = PendingCaptureReviewService().save_pending_box(
            captured.session,
            captured.context,
            "pending-001",
            label="Line 1",
        )

        capture = saved.session.captures[0]
        canvas_object = saved.session.canvas_objects[0]
        self.assertEqual((), saved.session.pending_captures)
        self.assertEqual("Line 1", capture.label)
        self.assertEqual("line", capture.geometry.kind.value)
        self.assertEqual(Point(1, 1), capture.geometry.start)
        self.assertEqual(Point(4, 1), capture.geometry.end)
        self.assertEqual(CanvasObjectType.LINE, canvas_object.object_type)
        self.assertEqual(CanvasWorkflowState.SAVED, canvas_object.workflow_state)

    def test_line_capture_uses_next_pending_id_after_saved_capture(self) -> None:
        tool = LineCaptureTool()
        context = tool.arm(InteractionContext())
        first = _drag_line(tool, _session(), context, Point(1, 1), Point(2, 1))
        saved = PendingCaptureReviewService().save_pending_box(
            first.session,
            first.context,
            "pending-001",
        )

        second = _drag_line(
            tool,
            saved.session,
            tool.arm(saved.context),
            Point(3, 1),
            Point(4, 1),
        )

        self.assertEqual("pending-002", second.session.pending_captures[0].id)


def _drag_line(
    tool: LineCaptureTool,
    session: SessionRecord,
    context: InteractionContext,
    start: Point,
    end: Point,
):
    started = tool.handle(session, context, CaptureGesture("drag_start", start, True))
    return tool.handle(started.session, started.context, CaptureGesture("drag_release", end, True))


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
