import tempfile
import unittest
from pathlib import Path

from metrology_process_planner.domains.geometry import Box
from metrology_process_planner.domains.session import (
    CanvasObject,
    CanvasObjectType,
    CanvasVisualFlag,
    CanvasWorkflowState,
    CaptureGeometry,
    PendingCapture,
    SessionMode,
    SessionRecord,
    SourceViewBinding,
)
from metrology_process_planner.persistence.json_store import SessionJsonStore
from metrology_process_planner.persistence.paths import SessionPaths
from metrology_process_planner.workflows.canvas_interaction_helpers import pending_crop_artifact

FIXTURES = Path(__file__).resolve().parent / "fixtures"


class CanvasSessionModelTests(unittest.TestCase):
    def test_canvas_object_round_trips_visual_and_parent_state(self) -> None:
        canvas_object = _canvas_object()

        loaded = CanvasObject.from_dict(canvas_object.to_dict())

        self.assertEqual(canvas_object, loaded)
        self.assertEqual("site-canvas", loaded.parent_id)
        self.assertIn(CanvasVisualFlag.SELECTED, loaded.visual_state)

    def test_pending_capture_round_trips_source_binding(self) -> None:
        pending = _pending_capture()

        loaded = PendingCapture.from_dict(pending.to_dict())

        self.assertEqual(pending, loaded)
        self.assertEqual("images/pending-001.png", loaded.image_artifact_path)
        self.assertEqual("top", loaded.source_view_binding.cell_name)

    def test_v1_session_loads_as_v5_with_empty_canvas_state(self) -> None:
        session = SessionJsonStore().load(FIXTURES / "sessions" / "simple_session")

        self.assertEqual("5.0.0", session.schema_version)
        self.assertEqual("1", session.schema.previous_version)
        self.assertEqual((), session.canvas_objects)
        self.assertEqual((), session.pending_captures)

    def test_session_round_trip_preserves_canvas_state(self) -> None:
        pending = _pending_capture()
        artifact = pending_crop_artifact(pending)
        artifacts = {artifact.id: artifact} if artifact is not None else {}
        session = SessionRecord(
            id="session-001",
            name="Canvas Session",
            mode=SessionMode.SIMPLE_CAPTURE,
            created_at="2026-06-23T20:00:00Z",
            updated_at="2026-06-23T20:00:00Z",
            canvas_objects=(_canvas_object(),),
            pending_captures=(pending,),
            artifacts=artifacts,
        )

        with tempfile.TemporaryDirectory() as temp_dir:
            paths = SessionPaths.for_folder(Path(temp_dir))
            SessionJsonStore().save(session, paths)
            loaded = SessionJsonStore().load(paths.folder)

        self.assertEqual("5.0.0", loaded.schema_version)
        self.assertEqual(session.canvas_objects, loaded.canvas_objects)
        self.assertEqual(session.pending_captures, loaded.pending_captures)
        self.assertIn("pending_capture-pending-001-pending_crop", loaded.artifacts)
        self.assertTrue(any(warning.code == "artifact_missing" for warning in loaded.warnings))


def _canvas_object() -> CanvasObject:
    return CanvasObject(
        id="canvas-001",
        session_id="session-001",
        record_id="pending-001",
        object_type=CanvasObjectType.SITE_BOX,
        parent_id="site-canvas",
        geometry=CaptureGeometry.box(Box(0, 0, 5, 5)),
        workflow_state=CanvasWorkflowState.PENDING,
        source_view_binding=SourceViewBinding(layout_name="demo", cell_name="top"),
        visual_state=(CanvasVisualFlag.SELECTED, CanvasVisualFlag.ACTIVE_PARENT),
        warning_ids=("warn-001",),
    )


def _pending_capture() -> PendingCapture:
    return PendingCapture(
        id="pending-001",
        session_id="session-001",
        canvas_object_id="canvas-001",
        object_type=CanvasObjectType.SITE_BOX,
        geometry=CaptureGeometry.box(Box(0, 0, 5, 5)),
        parent_id="site-canvas",
        created_at="2026-06-23T20:00:00Z",
        image_artifact_path="images/pending-001.png",
        source_view_binding=SourceViewBinding(layout_name="demo", cell_name="top"),
    )


if __name__ == "__main__":
    unittest.main()
