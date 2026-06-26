import unittest
from dataclasses import replace

from metrology_process_planner.app.bootstrap import build_app_services
from metrology_process_planner.app.commands import CommandId
from metrology_process_planner.domains.geometry import Point
from metrology_process_planner.domains.session import (
    CanvasVisualFlag,
    ModeCapabilities,
    ModeDefinition,
    ModeRegistry,
    SessionMode,
    SessionModeId,
    SessionRecord,
    SetupDefinition,
    SetupItemRecord,
    SetupState,
)
from metrology_process_planner.workflows import CanvasInteractionEngine, InteractionContext
from metrology_process_planner.workflows.editor import SessionDocumentBuilder


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


class CaptureSetupReadinessGuardTestsPart2(unittest.TestCase):
    def test_start_capture_command_blocks_stale_ready_flag_without_required_setup(self) -> None:
        services = build_app_services()
        stale_ready = replace(
            _session(SessionMode.CDSEM_MEASUREMENT),
            setup=SetupState(is_capture_ready=True),
        )
        services.session_editor_controller.open_document(
            SessionDocumentBuilder().build(stale_ready)
        )

        routed = services.command_router.route(CommandId.START_CAPTURE)

        current = services.session_editor_controller.current_document
        self.assertEqual("blocked", routed.status)
        self.assertIn("Optical Alignment Mark", routed.message)
        self.assertIn("SEM Alignment Mark", routed.message)
        self.assertEqual(
            "Complete required setup cards before starting site capture.",
            routed.next_ui_hint,
        )
        self.assertIsNotNone(current)
        assert current is not None
        self.assertFalse(current.session.workflow.active)

    def test_start_capture_command_continues_after_required_setup(self) -> None:
        services = build_app_services()
        ready = replace(
            _session(SessionMode.CDSEM_MEASUREMENT),
            setup=SetupState(
                items=(
                    _complete_alignment("optical_alignment"),
                    _complete_alignment("sem_alignment"),
                ),
                is_capture_ready=True,
            ),
        )
        services.session_editor_controller.open_document(SessionDocumentBuilder().build(ready))

        routed = services.command_router.route(CommandId.START_CAPTURE)

        current = services.session_editor_controller.current_document
        self.assertEqual("success", routed.status)
        self.assertIsNotNone(current)
        assert current is not None
        self.assertTrue(current.session.workflow.active)
        self.assertEqual("box_capture", current.session.workflow.stage)

    def test_external_setup_mode_blocks_capture_through_loaded_registry(self) -> None:
        registry = _external_setup_registry()
        source = replace(_session(SessionMode.SIMPLE_CAPTURE), mode=SessionModeId("external_setup"))

        session, context = _drag_box(source, mode_registry=registry)

        self.assertEqual((), session.pending_captures)
        self.assertIn("Optical Alignment Mark", context.messages[0])
        self.assertIn(CanvasVisualFlag.INVALID, session.canvas_objects[0].visual_state)

    def test_external_setup_mode_start_capture_command_uses_loaded_registry(self) -> None:
        registry = _external_setup_registry()
        services = build_app_services(mode_registry=registry)
        source = replace(_session(SessionMode.SIMPLE_CAPTURE), mode=SessionModeId("external_setup"))
        services.session_editor_controller.open_document(
            SessionDocumentBuilder(mode_registry=registry).build(source)
        )

        routed = services.command_router.route(CommandId.START_CAPTURE)

        current = services.session_editor_controller.current_document
        self.assertEqual("blocked", routed.status)
        self.assertIn("Optical Alignment Mark", routed.message)
        self.assertIsNotNone(current)
        assert current is not None
        self.assertFalse(current.session.workflow.active)
