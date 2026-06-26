import unittest
from dataclasses import replace

from metrology_process_planner.app.bootstrap import build_app_services
from metrology_process_planner.app.commands import CommandId
from metrology_process_planner.domains.session import (
    CanvasVisualFlag,
    SessionMode,
    SessionModeId,
    SetupState,
)
from metrology_process_planner.workflows.editor import SessionDocumentBuilder
from tests.capture_setup_readiness_fixtures import (
    complete_alignment as _complete_alignment,
)
from tests.capture_setup_readiness_fixtures import (
    drag_box as _drag_box,
)
from tests.capture_setup_readiness_fixtures import (
    external_setup_registry as _external_setup_registry,
)
from tests.capture_setup_readiness_fixtures import (
    session as _session,
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

    def test_start_capture_command_blocks_cdsem_planning_without_required_setup(self) -> None:
        services = build_app_services()
        stale_ready = replace(
            _session(SessionMode.CDSEM_PLANNING),
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

    def test_start_capture_command_continues_for_cdsem_planning_after_required_setup(self) -> None:
        services = build_app_services()
        ready = replace(
            _session(SessionMode.CDSEM_PLANNING),
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
