import unittest

from tests.klayout_boundary_fixtures import SourceLayoutTrap


class KLayoutCaptureAdapterBoundaryTests(unittest.TestCase):
    def test_klayout_line_gesture_adapter_uses_overlays_only(self) -> None:
        from metrology_process_planner.infrastructure.klayout.capture_adapter import (
            KLayoutCaptureGestureAdapter,
            KLayoutGestureEvent,
        )
        from metrology_process_planner.infrastructure.klayout.overlays import KLayoutOverlayBackend
        from metrology_process_planner.workflows import CanvasOverlayManager, OverlayCommandKind
        from tests.measurement_child_fixtures import saved_capture_session

        source_layout = SourceLayoutTrap()
        backend = KLayoutOverlayBackend(
            marker_factory=lambda command: ("marker", command.object_id)
        )
        adapter = KLayoutCaptureGestureAdapter(
            saved_capture_session(),
            CanvasOverlayManager(backend),
        )

        adapter.arm_line_capture("canvas-cap")
        ignored = adapter.handle(KLayoutGestureEvent("drag_start", 1, 1))
        started = adapter.handle(KLayoutGestureEvent("drag_start", 1, 1, True))
        adapter.handle(KLayoutGestureEvent("drag_update", 3, 1, True))
        released = adapter.handle(KLayoutGestureEvent("drag_release", 4, 1, True))

        self.assertFalse(ignored.handled)
        self.assertTrue(started.handled)
        self.assertTrue(released.handled)
        self.assertFalse(source_layout.mutated)
        self.assertEqual("meas-001", adapter.session.captures[0].measurements[0].id)
        self.assertEqual("canvas-cap", adapter.session.canvas_objects[1].parent_id)
        self.assertIn("canvas-001", {command.object_id for command in backend.commands})
        self.assertIn(
            OverlayCommandKind.ACTIVE_PARENT,
            {command.kind for command in backend.commands if command.object_id == "canvas-cap"},
        )

    def test_klayout_line_gesture_adapter_commits_profilometry_child_line(self) -> None:
        from metrology_process_planner.domains.session import SessionMode
        from metrology_process_planner.infrastructure.klayout.capture_adapter import (
            KLayoutCaptureGestureAdapter,
            KLayoutGestureEvent,
        )
        from metrology_process_planner.infrastructure.klayout.overlays import KLayoutOverlayBackend
        from metrology_process_planner.workflows import CanvasOverlayManager
        from metrology_process_planner.workflows.compound_capture import (
            arm_inner_feature_capture,
            profilometry_request,
        )
        from tests.compound_capture_fixtures import pending_parent

        source_layout = SourceLayoutTrap()
        backend = KLayoutOverlayBackend(
            marker_factory=lambda command: ("marker", command.object_id)
        )
        session = arm_inner_feature_capture(
            pending_parent(SessionMode.PROFILOMETRY_PLANNER),
            "pending-001",
            profilometry_request(),
        )
        adapter = KLayoutCaptureGestureAdapter(session, CanvasOverlayManager(backend))

        adapter.arm_line_capture("canvas-parent")
        adapter.handle(KLayoutGestureEvent("drag_start", 1, 1, True))
        adapter.handle(KLayoutGestureEvent("drag_update", 5, 5, True))
        released = adapter.handle(KLayoutGestureEvent("drag_release", 9, 9, True))

        pending = adapter.session.pending_captures[0]
        feature = dict(dict(pending.metadata)["compound"])["feature"]
        self.assertTrue(released.handled)
        self.assertFalse(source_layout.mutated)
        self.assertEqual("profilometry_line", feature["role"])
        self.assertEqual("profilometry_line", adapter.session.canvas_objects[1].object_type.value)
        self.assertEqual("canvas-parent", adapter.session.canvas_objects[1].parent_id)

    def test_klayout_adapter_leaves_navigation_unhandled_when_unarmed(self) -> None:
        from metrology_process_planner.infrastructure.klayout.capture_adapter import (
            KLayoutCaptureGestureAdapter,
            KLayoutGestureEvent,
        )
        from metrology_process_planner.infrastructure.klayout.overlays import KLayoutOverlayBackend
        from metrology_process_planner.workflows import CanvasOverlayManager
        from tests.measurement_child_fixtures import saved_capture_session

        backend = KLayoutOverlayBackend()
        adapter = KLayoutCaptureGestureAdapter(
            saved_capture_session(),
            CanvasOverlayManager(backend),
        )

        result = adapter.handle(KLayoutGestureEvent("drag_start", 1, 1, True))

        self.assertFalse(result.handled)
        self.assertEqual((), backend.commands)

class KLayoutStandaloneCaptureAdapterBoundaryTests(unittest.TestCase):
    def test_klayout_point_capture_commits_standalone_pending_capture(self) -> None:
        from metrology_process_planner.infrastructure.klayout.capture_adapter import (
            KLayoutCaptureGestureAdapter,
            KLayoutGestureEvent,
        )
        from metrology_process_planner.infrastructure.klayout.overlays import KLayoutOverlayBackend
        from metrology_process_planner.workflows import CanvasOverlayManager
        from tests.measurement_child_fixtures import saved_capture_session

        backend = KLayoutOverlayBackend()
        adapter = KLayoutCaptureGestureAdapter(
            saved_capture_session(),
            CanvasOverlayManager(backend),
        )

        adapter.arm_point_capture("canvas-cap")
        result = adapter.handle(KLayoutGestureEvent("click", 2, 2, True))

        self.assertTrue(result.handled)
        self.assertEqual(1, len(adapter.session.pending_captures))
        self.assertEqual("canvas-cap", adapter.session.pending_captures[0].parent_id)
        self.assertTrue(backend.commands)

    def test_klayout_line_capture_commits_standalone_pending_capture(self) -> None:
        from metrology_process_planner.infrastructure.klayout.capture_adapter import (
            KLayoutCaptureGestureAdapter,
            KLayoutGestureEvent,
        )
        from metrology_process_planner.infrastructure.klayout.overlays import KLayoutOverlayBackend
        from metrology_process_planner.workflows import CanvasOverlayManager
        from tests.measurement_child_fixtures import saved_capture_session

        backend = KLayoutOverlayBackend()
        adapter = KLayoutCaptureGestureAdapter(
            saved_capture_session(),
            CanvasOverlayManager(backend),
        )

        adapter.arm_line_capture()
        started = adapter.handle(KLayoutGestureEvent("drag_start", 1, 1, True))
        adapter.handle(KLayoutGestureEvent("drag_update", 3, 1, True))
        released = adapter.handle(KLayoutGestureEvent("drag_release", 4, 1, True))

        pending = adapter.session.pending_captures[0]
        line = adapter.session.canvas_objects[-1]
        self.assertTrue(started.handled)
        self.assertTrue(released.handled)
        self.assertEqual("line", pending.geometry.kind.value)
        self.assertEqual("line", line.object_type.value)
        self.assertIsNone(pending.parent_id)
        self.assertTrue(backend.commands)


if __name__ == "__main__":
    unittest.main()
