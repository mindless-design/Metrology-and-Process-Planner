import unittest

from metrology_process_planner.domains.geometry import Point
from metrology_process_planner.domains.session import CanvasObjectType, SessionMode
from metrology_process_planner.ui.capture import (
    BoxCaptureTool,
    CaptureGesture,
    CaptureGesturePolicy,
    CaptureToolPresenter,
    LineCaptureTool,
    PointCaptureTool,
)
from metrology_process_planner.workflows import InteractionContext
from metrology_process_planner.workflows.compound_capture import (
    arm_inner_feature_capture,
    ellipsometry_request,
)
from tests.compound_capture_fixtures import pending_parent
from tests.editor_render_fixtures import session, session_without_pending

if __name__ == "__main__":
    unittest.main()


class UiLayerRedesignTestsPart2(unittest.TestCase):
    def test_capture_tools_share_shift_gesture_policy_and_status_view_model(self) -> None:
        policy = CaptureGesturePolicy()
        context = InteractionContext()
        box_tool = BoxCaptureTool(policy=policy)
        armed = box_tool.arm(context)

        ignored = box_tool.handle(session(), armed, CaptureGesture("drag_start", Point(0, 0)))
        started = box_tool.handle(
            session(),
            armed,
            CaptureGesture("drag_start", Point(0, 0), shift_pressed=True),
        )
        status = CaptureToolPresenter().build(LineCaptureTool().arm(context, "parent-001"))
        point_status = CaptureToolPresenter().build(PointCaptureTool().arm(context))

        self.assertFalse(ignored.handled)
        self.assertTrue(started.handled)
        self.assertEqual("Left Shift + drag line", status.gesture_hint)
        self.assertEqual("Left Shift + click point", point_status.gesture_hint)
        self.assertTrue(
            policy.accepts(
                CanvasObjectType.SITE_BOX,
                CaptureGesture("drag_update", Point(1, 1), True),
            )
        )

    def test_point_capture_creates_standalone_pending_capture(self) -> None:
        tool = PointCaptureTool()
        current_session = session_without_pending()
        context = tool.arm(InteractionContext(), "parent-001")

        ignored = tool.handle(
            current_session,
            context,
            CaptureGesture("click", Point(1, 1)),
        )
        captured = tool.handle(
            current_session,
            context,
            CaptureGesture("click", Point(1, 1), shift_pressed=True),
        )

        self.assertFalse(ignored.handled)
        self.assertTrue(captured.handled)
        self.assertEqual(1, len(captured.session.pending_captures))
        self.assertEqual(Point(1, 1), captured.session.pending_captures[0].geometry.point)
        self.assertEqual("parent-001", captured.session.pending_captures[0].parent_id)

    def test_point_capture_adds_ellipsometry_child_during_compound_workflow(self) -> None:
        tool = PointCaptureTool()
        current_session = arm_inner_feature_capture(
            pending_parent(SessionMode.ELLIPSOMETRY_PLANNER),
            "pending-001",
            ellipsometry_request(),
        )
        context = tool.arm(InteractionContext(), "canvas-parent")

        result = tool.handle(
            current_session,
            context,
            CaptureGesture("click", Point(4, 4), shift_pressed=True),
        )

        self.assertTrue(result.handled)
        self.assertEqual(2, len(result.session.canvas_objects))
        self.assertEqual(
            CanvasObjectType.ELLIPSOMETRY_POINT,
            result.session.canvas_objects[1].object_type,
        )
