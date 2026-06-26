import unittest
from dataclasses import replace
from pathlib import Path
from tempfile import TemporaryDirectory

from metrology_process_planner.domains.geometry import Point
from metrology_process_planner.domains.session import SessionMode, WorkflowState
from metrology_process_planner.persistence.json_store import SessionJsonStore
from metrology_process_planner.persistence.paths import SessionPaths
from metrology_process_planner.workflows import CanvasInteractionEngine, InteractionContext
from tests.editor_render_fixtures import empty_session


class SetupCaptureCommitTests(unittest.TestCase):
    def test_setup_origin_point_capture_updates_durable_origin(self) -> None:
        source = _setup_capture_session(SessionMode.OPTICAL_METROLOGY, "origin_point_capture")

        captured = _shift_click_setup_point(source, Point(12, 34))

        self.assertEqual((), captured.pending_captures)
        self.assertIsNotNone(captured.setup.origin)
        assert captured.setup.origin is not None
        self.assertEqual("origin", captured.setup.coordinate_mode)
        self.assertEqual(12, captured.setup.origin.point.x)
        self.assertEqual(34, captured.setup.origin.point.y)
        self.assertEqual("origin", captured.canvas_objects[0].record_id)
        self.assertEqual("point", captured.canvas_objects[0].object_type.value)

    def test_setup_origin_point_survives_save_and_reopen(self) -> None:
        captured = _shift_click_setup_point(
            _setup_capture_session(SessionMode.CDSEM_CAPTURE, "origin_point_capture"),
            Point(7, 9),
        )

        with TemporaryDirectory() as temp_dir:
            paths = SessionPaths.for_folder(Path(temp_dir))
            SessionJsonStore().save(captured, paths)
            loaded = SessionJsonStore().load(paths.folder)

        self.assertIsNotNone(loaded.setup.origin)
        assert loaded.setup.origin is not None
        self.assertEqual(7, loaded.setup.origin.point.x)
        self.assertEqual(9, loaded.setup.origin.point.y)

    def test_setup_alignment_capture_completes_required_optical_stage(self) -> None:
        source = _setup_capture_session(SessionMode.OPTICAL_METROLOGY, "alignment_box_capture")

        captured = _shift_drag_setup_box(source)

        self.assertEqual((), captured.pending_captures)
        item = captured.setup.items[0]
        self.assertEqual("optical_alignment", item.id)
        self.assertEqual("complete", item.status)
        self.assertIn("optical_alignment_image", item.artifact_refs)
        artifact = captured.artifacts[item.artifact_refs["optical_alignment_image"]]
        self.assertEqual("setup", artifact.owner.owner_type)
        self.assertEqual("optical_alignment", artifact.owner.owner_id)
        self.assertFalse(captured.workflow.active)
        self.assertEqual("", captured.workflow.stage)
        self.assertEqual("", captured.workflow.active_primitive)
        self.assertIsNone(captured.workflow.pending_item_ref)

    def test_setup_origin_reference_capture_creates_optional_reference_artifact(self) -> None:
        source = _setup_capture_session(
            SessionMode.OPTICAL_METROLOGY,
            "origin_reference_box_capture",
        )

        captured = _shift_drag_setup_box(source)

        self.assertEqual((), captured.pending_captures)
        item = captured.setup.items[0]
        self.assertEqual("origin_reference", item.id)
        self.assertEqual("origin_reference_box_capture", item.item_type)
        self.assertEqual("complete", item.status)
        self.assertFalse(item.metadata["required"])
        self.assertIn("origin_reference_image", item.artifact_refs)
        artifact = captured.artifacts[item.artifact_refs["origin_reference_image"]]
        self.assertEqual("setup", artifact.owner.owner_type)
        self.assertEqual("origin_reference", artifact.owner.owner_id)
        self.assertEqual("origin_reference_image", artifact.owner.role)
        self.assertEqual("images/setup-origin_reference.png", artifact.relative_path)
        self.assertFalse(captured.workflow.active)

    def test_setup_alignment_capture_state_survives_save_and_reopen(self) -> None:
        captured = _shift_drag_setup_box(
            _setup_capture_session(SessionMode.CDSEM_CAPTURE, "sem_alignment_box_capture")
        )

        with TemporaryDirectory() as temp_dir:
            paths = SessionPaths.for_folder(Path(temp_dir))
            SessionJsonStore().save(captured, paths)
            loaded = SessionJsonStore().load(paths.folder)

        item = loaded.setup.items[0]
        self.assertEqual("sem_alignment", item.id)
        self.assertEqual("complete", item.status)
        self.assertIn(item.artifact_refs["sem_alignment_image"], loaded.artifacts)

    def test_setup_origin_reference_state_survives_save_and_reopen(self) -> None:
        captured = _shift_drag_setup_box(
            _setup_capture_session(SessionMode.OPTICAL_METROLOGY, "origin_reference_box_capture")
        )

        with TemporaryDirectory() as temp_dir:
            paths = SessionPaths.for_folder(Path(temp_dir))
            SessionJsonStore().save(captured, paths)
            loaded = SessionJsonStore().load(paths.folder)

        item = loaded.setup.items[0]
        self.assertEqual("origin_reference", item.id)
        self.assertEqual("complete", item.status)
        self.assertIn(item.artifact_refs["origin_reference_image"], loaded.artifacts)


def _setup_capture_session(mode: SessionMode, stage: str):
    return replace(
        empty_session(),
        mode=mode,
        workflow=WorkflowState(
            active=True,
            stage=stage,
            active_mode=mode.value,
            active_primitive="site_box",
            pending_item_ref=f"setup:{stage}",
        ),
    )


def _shift_drag_setup_box(source):
    engine = CanvasInteractionEngine()
    context = engine.arm_box_capture(InteractionContext())
    started = engine.start_drag(source, context, Point(0, 0), shift_pressed=True)
    released = engine.release_drag(started.session, started.context, Point(5, 5), True)
    return released.session


def _shift_click_setup_point(source, point: Point):
    engine = CanvasInteractionEngine()
    context = engine.arm_point_capture(InteractionContext())
    started = engine.start_drag(source, context, point, shift_pressed=True)
    return started.session


if __name__ == "__main__":
    unittest.main()
