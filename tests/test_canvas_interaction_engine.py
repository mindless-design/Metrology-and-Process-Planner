import unittest
from typing import Optional

from metrology_process_planner.domains.geometry import Point
from metrology_process_planner.domains.session import (
    CanvasObjectType,
    CanvasVisualFlag,
    CanvasWorkflowState,
    CaptureRecord,
    SessionMode,
    SessionRecord,
)
from metrology_process_planner.workflows import (
    CanvasInteractionEngine,
    InteractionContext,
    PendingCaptureReviewService,
)


class CanvasInteractionEngineTests(unittest.TestCase):
    def test_unarmed_drag_is_not_handled(self) -> None:
        result = CanvasInteractionEngine().start_drag(
            _session(),
            InteractionContext(),
            Point(0, 0),
            shift_pressed=True,
        )

        self.assertFalse(result.handled)
        self.assertEqual((), result.session.canvas_objects)

    def test_armed_box_capture_requires_shift_gesture(self) -> None:
        engine = CanvasInteractionEngine()
        context = engine.arm_box_capture(InteractionContext())

        result = engine.start_drag(_session(), context, Point(0, 0), shift_pressed=False)

        self.assertFalse(result.handled)
        self.assertEqual((), result.session.canvas_objects)

    def test_shift_drag_commits_pending_selected_active_parent_box(self) -> None:
        session, context = _pending_box()

        canvas_object = session.canvas_objects[0]

        self.assertEqual("pending-001", session.pending_captures[0].id)
        self.assertIn("pending_capture-pending-001-pending_crop", session.artifacts)
        self.assertEqual(CanvasWorkflowState.PENDING, canvas_object.workflow_state)
        self.assertEqual("pending-001", canvas_object.record_id)
        self.assertIn(CanvasVisualFlag.SELECTED, canvas_object.visual_state)
        self.assertIn(CanvasVisualFlag.ACTIVE_PARENT, canvas_object.visual_state)
        self.assertEqual("canvas-001", context.active_parent_id)

    def test_save_pending_box_creates_capture_and_preserves_canvas_object(self) -> None:
        session, context = _pending_box()

        result = PendingCaptureReviewService().save_pending_box(
            session,
            context,
            "pending-001",
            label="Site 1",
            notes="Ready",
        )
        canvas_object = result.session.canvas_objects[0]

        self.assertEqual((), result.session.pending_captures)
        self.assertEqual("cap-001", result.session.captures[0].id)
        artifact = result.session.artifacts["capture-cap-001-crop"]
        self.assertEqual("images/pending-001.png", artifact.relative_path)
        self.assertEqual(
            {"crop": "capture-cap-001-crop"},
            result.session.captures[0].artifact_refs,
        )
        self.assertEqual("cap-001", canvas_object.record_id)
        self.assertEqual(CanvasWorkflowState.SAVED, canvas_object.workflow_state)
        self.assertIn(CanvasVisualFlag.SELECTED, canvas_object.visual_state)

    def test_discard_pending_removes_only_pending_state(self) -> None:
        session, context = _pending_box(session=_session_with_saved_capture())

        result = PendingCaptureReviewService().discard_pending(session, context, "pending-001")

        self.assertEqual(("images/pending-001.png",), result.artifact_paths_to_remove)
        self.assertEqual((), result.session.pending_captures)
        self.assertEqual((), result.session.canvas_objects)
        self.assertEqual("cap-existing", result.session.captures[0].id)

    def test_retake_pending_rearms_original_parent_context(self) -> None:
        session, context = _pending_box(parent_id="canvas-parent")

        result = PendingCaptureReviewService().retake_pending(session, context, "pending-001")

        self.assertEqual(CanvasObjectType.SITE_BOX, result.context.armed_object_type)
        self.assertEqual("canvas-parent", result.context.active_parent_id)
        self.assertEqual((), result.session.pending_captures)

    def test_exit_capture_removes_live_preview_but_not_saved_records(self) -> None:
        engine = CanvasInteractionEngine()
        context = engine.arm_box_capture(InteractionContext())
        started = engine.start_drag(_session_with_saved_capture(), context, Point(0, 0), True)

        exited = engine.exit_capture(started.session, started.context)

        self.assertEqual((), exited.session.canvas_objects)
        self.assertEqual("cap-existing", exited.session.captures[0].id)
        self.assertIsNone(exited.context.armed_object_type)

def _pending_box(
    session: Optional[SessionRecord] = None,
    parent_id: str = "",
) -> tuple[SessionRecord, InteractionContext]:
    engine = CanvasInteractionEngine()
    active_session = session if session is not None else _session()
    parent = parent_id or None
    context = engine.arm_box_capture(InteractionContext(), parent_id=parent)
    started = engine.start_drag(active_session, context, Point(0, 0), shift_pressed=True)
    released = engine.release_drag(started.session, started.context, Point(5, 5), True)
    return released.session, released.context


def _session() -> SessionRecord:
    return SessionRecord(
        id="session-001",
        name="Demo Session",
        mode=SessionMode.SIMPLE_CAPTURE,
        created_at="2026-06-23T20:00:00Z",
        updated_at="2026-06-23T20:00:00Z",
    )


def _session_with_saved_capture() -> SessionRecord:
    return _session().add_capture(
        CaptureRecord(
            id="cap-existing",
            label="Saved",
            geometry=_session().captures[0].geometry if _session().captures else _box_geometry(),
            created_at="2026-06-23T20:00:00Z",
        )
    )


def _box_geometry():
    from metrology_process_planner.domains.session import CaptureGeometry

    return CaptureGeometry.box(__box())


def __box():
    from metrology_process_planner.domains.geometry import Box

    return Box(0, 0, 5, 5)


if __name__ == "__main__":
    unittest.main()
