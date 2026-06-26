import unittest
from dataclasses import replace

from metrology_process_planner.domains.session import (
    CanvasVisualFlag,
    SessionMode,
    SetupState,
    WorkflowState,
)
from tests.capture_setup_readiness_fixtures import (
    complete_alignment as _complete_alignment,
)
from tests.capture_setup_readiness_fixtures import (
    drag_box as _drag_box,
)
from tests.capture_setup_readiness_fixtures import (
    session as _session,
)

if __name__ == "__main__":
    unittest.main()


class CaptureSetupReadinessGuardTestsPart1(unittest.TestCase):
    def test_optical_site_capture_blocks_until_required_alignment_is_complete(self) -> None:
        session, context = _drag_box(_session(SessionMode.OPTICAL_METROLOGY))

        self.assertEqual((), session.pending_captures)
        self.assertIn("Optical Alignment Mark", context.messages[0])
        self.assertIn(CanvasVisualFlag.INVALID, session.canvas_objects[0].visual_state)

    def test_optical_site_capture_continues_after_required_alignment(self) -> None:
        ready = replace(
            _session(SessionMode.OPTICAL_METROLOGY),
            setup=SetupState(items=(_complete_alignment("optical_alignment"),)),
        )

        session, _context = _drag_box(ready)

        self.assertEqual("pending-001", session.pending_captures[0].id)

    def test_setup_alignment_capture_is_allowed_before_capture_readiness(self) -> None:
        setup_capture = replace(
            _session(SessionMode.OPTICAL_METROLOGY),
            workflow=WorkflowState(active=True, stage="alignment_box_capture"),
        )

        session, context = _drag_box(setup_capture)

        self.assertEqual((), session.pending_captures)
        self.assertEqual("optical_alignment", session.setup.items[0].id)
        self.assertEqual("images/setup-optical_alignment.png", context.artifact_requests[0])

    def test_cdsem_site_capture_blocks_until_both_required_alignments_complete(self) -> None:
        session, context = _drag_box(_session(SessionMode.CDSEM_CAPTURE))

        self.assertEqual((), session.pending_captures)
        self.assertIn("Optical Alignment Mark", context.messages[0])
        self.assertIn("SEM Alignment Mark", context.messages[0])

        partial = replace(
            _session(SessionMode.CDSEM_CAPTURE),
            setup=SetupState(items=(_complete_alignment("optical_alignment"),)),
        )
        session, context = _drag_box(partial)

        self.assertEqual((), session.pending_captures)
        self.assertNotIn("Optical Alignment Mark", context.messages[0])
        self.assertIn("SEM Alignment Mark", context.messages[0])

    def test_cdsem_measurement_capture_blocks_until_both_required_alignments_complete(self) -> None:
        session, context = _drag_box(_session(SessionMode.CDSEM_MEASUREMENT))

        self.assertEqual((), session.pending_captures)
        self.assertIn("Optical Alignment Mark", context.messages[0])
        self.assertIn("SEM Alignment Mark", context.messages[0])

        partial = replace(
            _session(SessionMode.CDSEM_MEASUREMENT),
            setup=SetupState(items=(_complete_alignment("optical_alignment"),)),
        )
        session, context = _drag_box(partial)

        self.assertEqual((), session.pending_captures)
        self.assertNotIn("Optical Alignment Mark", context.messages[0])
        self.assertIn("SEM Alignment Mark", context.messages[0])

    def test_cdsem_planning_capture_blocks_until_both_required_alignments_complete(self) -> None:
        session, context = _drag_box(_session(SessionMode.CDSEM_PLANNING))

        self.assertEqual((), session.pending_captures)
        self.assertIn("Optical Alignment Mark", context.messages[0])
        self.assertIn("SEM Alignment Mark", context.messages[0])

        partial = replace(
            _session(SessionMode.CDSEM_PLANNING),
            setup=SetupState(items=(_complete_alignment("optical_alignment"),)),
        )
        session, context = _drag_box(partial)

        self.assertEqual((), session.pending_captures)
        self.assertNotIn("Optical Alignment Mark", context.messages[0])
        self.assertIn("SEM Alignment Mark", context.messages[0])

    def test_cdsem_site_capture_continues_after_required_alignments(self) -> None:
        ready = replace(
            _session(SessionMode.CDSEM_CAPTURE),
            setup=SetupState(
                items=(
                    _complete_alignment("optical_alignment"),
                    _complete_alignment("sem_alignment"),
                ),
            ),
        )

        session, _context = _drag_box(ready)

        self.assertEqual("pending-001", session.pending_captures[0].id)

    def test_cdsem_measurement_capture_continues_after_required_alignments(self) -> None:
        ready = replace(
            _session(SessionMode.CDSEM_MEASUREMENT),
            setup=SetupState(
                items=(
                    _complete_alignment("optical_alignment"),
                    _complete_alignment("sem_alignment"),
                ),
            ),
        )

        session, _context = _drag_box(ready)

        self.assertEqual("pending-001", session.pending_captures[0].id)

    def test_cdsem_planning_capture_continues_after_required_alignments(self) -> None:
        ready = replace(
            _session(SessionMode.CDSEM_PLANNING),
            setup=SetupState(
                items=(
                    _complete_alignment("optical_alignment"),
                    _complete_alignment("sem_alignment"),
                ),
            ),
        )

        session, _context = _drag_box(ready)

        self.assertEqual("pending-001", session.pending_captures[0].id)
