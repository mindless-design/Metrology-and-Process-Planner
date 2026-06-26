import unittest
from dataclasses import replace

from metrology_process_planner.domains.geometry import Point
from metrology_process_planner.domains.session import (
    CanvasVisualFlag,
    ModeCapabilities,
    ModeDefinition,
    ModeRegistry,
    SessionMode,
    SessionRecord,
    SetupDefinition,
    SetupItemRecord,
    SetupState,
    WorkflowState,
)
from metrology_process_planner.workflows import CanvasInteractionEngine, InteractionContext


def _drag_box(source: SessionRecord, mode_registry: ModeRegistry | None = None):
    engine = CanvasInteractionEngine(mode_registry=mode_registry)
    context = engine.arm_box_capture(InteractionContext())
    started = engine.start_drag(source, context, Point(0, 0), shift_pressed=True)
    result = engine.release_drag(started.session, started.context, Point(5, 5), True)
    return result.session, result

def _session(mode: SessionMode) -> SessionRecord:
    return SessionRecord(
        id="session-setup-readiness",
        name="Setup Readiness",
        mode=mode,
        created_at="2026-06-25T00:00:00Z",
        updated_at="2026-06-25T00:00:00Z",
    )

def _complete_alignment(item_id: str) -> SetupItemRecord:
    item_type = (
        "sem_alignment_box_capture"
        if item_id == "sem_alignment"
        else "alignment_box_capture"
    )
    label = "SEM Alignment Mark" if item_id == "sem_alignment" else "Optical Alignment Mark"
    return SetupItemRecord(
        item_id,
        item_type,
        label,
        "complete",
        metadata={"required": True},
    )

def _external_setup_registry() -> ModeRegistry:
    return ModeRegistry(
        (
            ModeDefinition(
                "external_setup",
                "External Setup",
                family="metrology",
                capabilities=ModeCapabilities(uses_setup_guide=True),
                setup=SetupDefinition(
                    required=True,
                    can_skip=False,
                    stage_types=("required_optical_alignment_mark",),
                ),
            ),
        )
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
