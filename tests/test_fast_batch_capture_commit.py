import unittest

from metrology_process_planner.domains.geometry import Box, Point
from metrology_process_planner.domains.session import (
    CanvasWorkflowState,
    CaptureGeometry,
    CaptureRecord,
    CaptureSequenceDefinition,
    ModeDefinition,
    ModeRegistry,
    SessionMode,
    SessionModeId,
    SessionRecord,
)
from metrology_process_planner.workflows import CanvasInteractionEngine, InteractionContext
from metrology_process_planner.workflows.editor import (
    DefaultSessionModeAdapter,
    SessionDocumentBuilder,
)
from metrology_process_planner.workflows.editor.view_models import EditorActionType


class FastBatchCaptureCommitTests(unittest.TestCase):
    def test_shift_drag_auto_saves_capture_without_pending_review(self) -> None:
        session, _context = _drag_box(_session())

        canvas_object = session.canvas_objects[0]
        document = SessionDocumentBuilder().build(session)

        self.assertEqual((), session.pending_captures)
        self.assertEqual("cap-001", session.captures[0].id)
        self.assertEqual(1, session.captures[0].sequence)
        self.assertEqual("Capture 001", session.captures[0].label)
        self.assertEqual(CanvasWorkflowState.SAVED, canvas_object.workflow_state)
        self.assertEqual("cap-001", canvas_object.record_id)
        self.assertIn("capture-cap-001-crop", session.artifacts)
        self.assertIn("capture-cap-001-site_image", session.artifacts)
        self.assertIn("capture:cap-001", document.items_by_id)
        self.assertIn("Saved Captures", _group_labels(document))
        self.assertNotIn("Pending", _group_labels(document))
        self.assertNotIn(
            EditorActionType.PENDING_SAVE,
            _visible_action_types(document),
        )
        self.assertIn(
            EditorActionType.ADD_MEASUREMENT,
            _visible_action_types(document, "capture:cap-001"),
        )

    def test_shift_drag_uses_next_stable_batch_label(self) -> None:
        existing = CaptureRecord(
            id="cap-007",
            label="Capture 007",
            geometry=CaptureGeometry.box(Box(0, 0, 1, 1)),
            created_at="2026-06-23T20:00:00Z",
            sequence=7,
        )

        session, _context = _drag_box(_session().add_capture(existing))

        self.assertEqual(("Capture 007", "Capture 008"), _capture_labels(session))
        self.assertEqual((7, 8), tuple(capture.sequence for capture in session.captures))
        self.assertEqual("cap-008", session.captures[-1].id)

    def test_loaded_batch_mode_auto_saves_with_custom_label_defaults(self) -> None:
        registry = ModeRegistry(
            (
                ModeDefinition(
                    "external_batch",
                    "External Batch",
                    capture=CaptureSequenceDefinition(
                        review=False,
                        site_role="external_site",
                        saved_capture_type="external_region",
                        repeat_label_template="External {sequence:02d}",
                    ),
                ),
            )
        )

        session, _context = _drag_box(_session(SessionModeId("external_batch")), registry)
        capture = session.captures[0]

        self.assertEqual((), session.pending_captures)
        self.assertEqual("External 01", capture.label)
        self.assertEqual("external_site", capture.role)
        self.assertEqual("external_region", capture.type)
        self.assertEqual("External 01", capture.metadata["label"])
        self.assertEqual("external_site", capture.metadata["capture_role"])
        self.assertEqual("external_region", capture.metadata["capture_type"])


def _drag_box(
    session: SessionRecord,
    mode_registry: ModeRegistry | None = None,
) -> tuple[SessionRecord, InteractionContext]:
    engine = CanvasInteractionEngine(mode_registry=mode_registry)
    context = engine.arm_box_capture(InteractionContext())
    started = engine.start_drag(session, context, Point(0, 0), shift_pressed=True)
    released = engine.release_drag(started.session, started.context, Point(5, 5), True)
    return released.session, released.context


def _session(mode: SessionMode | SessionModeId = SessionMode.FAST_BATCH_CAPTURE) -> SessionRecord:
    return SessionRecord(
        id="session-001",
        name="Fast Batch Session",
        mode=mode,
        created_at="2026-06-23T20:00:00Z",
        updated_at="2026-06-23T20:00:00Z",
    )


def _group_labels(document: object) -> tuple[str, ...]:
    return tuple(group.label for group in document.navigator_groups)


def _visible_action_types(
    document: object,
    item_id: str = "dashboard",
) -> tuple[EditorActionType, ...]:
    return tuple(
        action.action_type
        for action in DefaultSessionModeAdapter().actions(
            document.session,
            document.items_by_id[item_id],
        )
    )


def _capture_labels(session: SessionRecord) -> tuple[str, ...]:
    return tuple(capture.label for capture in session.captures)


if __name__ == "__main__":
    unittest.main()
