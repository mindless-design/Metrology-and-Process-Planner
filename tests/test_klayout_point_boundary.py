import unittest


class KLayoutPointBoundaryTests(unittest.TestCase):
    def test_klayout_point_gesture_adapter_commits_ellipsometry_child_point(self) -> None:
        from metrology_process_planner.domains.session import SessionMode
        from metrology_process_planner.infrastructure.klayout.capture_adapter import (
            KLayoutCaptureGestureAdapter,
            KLayoutGestureEvent,
        )
        from metrology_process_planner.infrastructure.klayout.overlays import KLayoutOverlayBackend
        from metrology_process_planner.workflows import CanvasOverlayManager
        from metrology_process_planner.workflows.compound_capture import (
            arm_inner_feature_capture,
            ellipsometry_request,
        )
        from tests.compound_capture_fixtures import pending_parent

        source_layout = SourceLayoutTrap()
        backend = KLayoutOverlayBackend(lambda command: ("marker", command.object_id))
        session = arm_inner_feature_capture(
            pending_parent(SessionMode.ELLIPSOMETRY_PLANNER),
            "pending-001",
            ellipsometry_request(),
        )
        adapter = KLayoutCaptureGestureAdapter(session, CanvasOverlayManager(backend))

        adapter.arm_point_capture("canvas-parent")
        ignored = adapter.handle(KLayoutGestureEvent("click", 5, 5))
        clicked = adapter.handle(KLayoutGestureEvent("click", 5, 5, True))

        pending = adapter.session.pending_captures[0]
        feature = dict(dict(pending.metadata)["compound"])["feature"]
        child = adapter.session.canvas_objects[1]
        self.assertFalse(ignored.handled)
        self.assertTrue(clicked.handled)
        self.assertFalse(source_layout.mutated)
        self.assertEqual("ellipsometry_point", feature["role"])
        self.assertEqual("ellipsometry_point", child.object_type.value)
        self.assertEqual("canvas-parent", child.parent_id)
        self.assertIn(child.id, {command.object_id for command in backend.commands})


class SourceLayoutTrap:
    def __init__(self) -> None:
        self.mutated = False

    def insert_shape(self) -> None:
        self.mutated = True


if __name__ == "__main__":
    unittest.main()
