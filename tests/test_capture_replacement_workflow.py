import unittest
from dataclasses import replace

from metrology_process_planner.domains.geometry import Box, Point
from metrology_process_planner.domains.session import (
    CanvasObject,
    CanvasObjectType,
    CanvasWorkflowState,
    CaptureGeometry,
    CaptureRecord,
    SessionMode,
    SessionRecord,
    WorkflowState,
)
from metrology_process_planner.workflows import (
    CanvasInteractionEngine,
    InteractionContext,
    PendingCaptureReviewService,
)
from metrology_process_planner.workflows.editor import (
    EditorAction,
    EditorActionDispatcher,
    EditorActionType,
    SessionDocumentBuilder,
)


class CaptureReplacementWorkflowTests(unittest.TestCase):
    def test_replace_capture_arms_shared_capture_workflow(self) -> None:
        document = SessionDocumentBuilder().build(_session_with_saved_capture())

        result = EditorActionDispatcher().dispatch(
            document,
            EditorAction(
                EditorActionType.REPLACE_SITE_BOX,
                "Replace Capture",
                "capture:cap-existing",
            ),
        )

        self.assertEqual("success", result.status)
        self.assertTrue(result.document.session.workflow.active)
        self.assertEqual("capture", result.document.session.workflow.stage)
        self.assertEqual("replacement_box", result.document.session.workflow.active_primitive)
        self.assertEqual("cap-existing", result.document.session.workflow.pending_item_ref)

    def test_pending_replacement_save_reuses_capture_id_and_supersedes_old_canvas(self) -> None:
        session, context = _pending_replacement_box()
        pending = session.pending_captures[0]

        result = PendingCaptureReviewService().save_pending_box(session, context, pending.id)

        self.assertEqual((), result.session.pending_captures)
        self.assertEqual(1, len(result.session.captures))
        self.assertEqual("cap-existing", result.session.captures[0].id)
        self.assertEqual(7, result.session.captures[0].sequence)
        self.assertEqual("Saved", result.session.captures[0].label)
        self.assertEqual("Existing notes", result.session.captures[0].notes)
        self.assertEqual(Box(0, 0, 5, 5), result.session.captures[0].geometry.bounds)
        self.assertFalse(result.session.workflow.active)
        self.assertEqual("", result.session.workflow.stage)
        old_canvas = result.session.canvas_objects[0]
        new_canvas = result.session.canvas_objects[1]
        self.assertEqual(CanvasWorkflowState.SUPERSEDED, old_canvas.workflow_state)
        self.assertFalse(old_canvas.visible)
        self.assertFalse(old_canvas.selectable)
        self.assertEqual("cap-existing", new_canvas.record_id)
        self.assertEqual(CanvasWorkflowState.SAVED, new_canvas.workflow_state)


def _pending_replacement_box() -> tuple[SessionRecord, InteractionContext]:
    engine = CanvasInteractionEngine()
    context = engine.arm_box_capture(InteractionContext())
    started = engine.start_drag(_session_armed_for_replacement(), context, Point(0, 0), True)
    released = engine.release_drag(started.session, started.context, Point(5, 5), True)
    return released.session, released.context


def _session_armed_for_replacement() -> SessionRecord:
    return replace(
        _session_with_saved_capture(),
        workflow=WorkflowState(
            active=True,
            stage="capture",
            active_primitive="replacement_box",
            pending_item_ref="cap-existing",
        ),
    )


def _session_with_saved_capture() -> SessionRecord:
    capture = CaptureRecord(
        id="cap-existing",
        label="Saved",
        notes="Existing notes",
        geometry=CaptureGeometry.box(Box(10, 10, 20, 20)),
        created_at="2026-06-23T20:00:00Z",
        sequence=7,
    )
    canvas = CanvasObject(
        "canvas-existing",
        "session-001",
        "cap-existing",
        CanvasObjectType.SITE_BOX,
        None,
        capture.geometry,
        CanvasWorkflowState.SAVED,
    )
    return replace(
        _base_session().add_capture(capture),
        canvas_objects=(canvas,),
    )


def _base_session() -> SessionRecord:
    return SessionRecord(
        id="session-001",
        name="Demo Session",
        mode=SessionMode.SIMPLE_CAPTURE,
        created_at="2026-06-23T20:00:00Z",
        updated_at="2026-06-23T20:00:00Z",
    )


if __name__ == "__main__":
    unittest.main()
