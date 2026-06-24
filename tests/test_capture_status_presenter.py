import unittest
from dataclasses import replace

from metrology_process_planner.domains.geometry import Point
from metrology_process_planner.domains.session import (
    CanvasObjectType,
    WorkflowState,
)
from metrology_process_planner.ui.capture import (
    CaptureGesture,
    CaptureGesturePolicy,
    capture_status_from_session,
)
from metrology_process_planner.ui.session_editor.header import status_text
from metrology_process_planner.ui.setup_guide import SetupGuidePresenter
from metrology_process_planner.workflows.editor import SessionDocumentBuilder
from tests.editor_render_fixtures import session


class CaptureStatusPresenterTests(unittest.TestCase):
    def test_session_workflow_builds_armed_box_status(self) -> None:
        source = _session_with_primitive(CanvasObjectType.SITE_BOX.value, "capture:site-001")

        status = capture_status_from_session(source)

        self.assertTrue(status.armed)
        self.assertEqual("site_box", status.primitive)
        self.assertEqual("Left Shift + drag box", status.gesture_hint)
        self.assertIn("hold Left Shift and drag a box", status.message)
        self.assertIn("capture:site-001", status.message)

    def test_editor_status_prefers_armed_capture_guidance(self) -> None:
        source = _session_with_primitive(CanvasObjectType.PROFILOMETRY_LINE.value)
        document = SessionDocumentBuilder().build(source)

        self.assertEqual(
            "Line capture armed: hold Left Shift and drag a line on the layout canvas.",
            status_text(document),
        )

    def test_setup_guide_carries_capture_status_message(self) -> None:
        source = _session_with_primitive(CanvasObjectType.ELLIPSOMETRY_POINT.value)

        view_model = SetupGuidePresenter().build(source)

        self.assertIn("Point capture armed", view_model.capture_status_message)
        self.assertIn("hold Left Shift and click a point", view_model.capture_status_message)

    def test_unknown_primitive_reports_navigation_active(self) -> None:
        source = _session_with_primitive("future_shape")

        status = capture_status_from_session(source)

        self.assertFalse(status.armed)
        self.assertEqual(
            "Unknown capture primitive 'future_shape'; KLayout navigation is active.",
            status.message,
        )

    def test_policy_accepts_mode_specific_point_primitive(self) -> None:
        policy = CaptureGesturePolicy()

        self.assertTrue(
            policy.accepts(
                CanvasObjectType.ELLIPSOMETRY_POINT,
                CaptureGesture("click", Point(0, 0), shift_pressed=True),
            )
        )


def _session_with_primitive(primitive: str, parent_id: str | None = None):
    return replace(
        session(),
        workflow=WorkflowState(
            active=bool(primitive),
            stage="capture",
            active_primitive=primitive,
            pending_item_ref=parent_id,
        ),
    )


if __name__ == "__main__":
    unittest.main()
