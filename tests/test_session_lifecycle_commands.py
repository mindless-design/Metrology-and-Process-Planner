import unittest
from dataclasses import replace

from metrology_process_planner.app.bootstrap import build_app_services
from metrology_process_planner.app.commands import CommandId
from metrology_process_planner.domains.session import WarningRecord
from metrology_process_planner.workflows.editor import SessionDocumentBuilder, mark_metadata_edit
from tests.editor_render_fixtures import session, session_without_pending


class SessionLifecycleCommandTests(unittest.TestCase):
    def test_end_active_session_closes_modeless_session_surfaces(self) -> None:
        services = build_app_services()
        source = session_without_pending()
        services.session_editor_controller.open_document(SessionDocumentBuilder().build(source))
        services.setup_guide_controller.set_active_session(source)
        services.setup_guide_controller.open_current()
        services.diagnostics_controller.set_active_session(source)
        services.diagnostics_controller.open_current()
        services.command_router.route(CommandId.START_BOX_CAPTURE)

        result = services.command_router.route(CommandId.END_ACTIVE_SESSION)

        self.assertEqual("success", result.status)
        self.assertIsNone(services.session_editor_controller.current_document)
        self.assertIsNone(services.setup_guide_controller.active_session)
        self.assertIsNone(services.diagnostics_controller.active_session)
        self.assertIsNone(services.capture_command_service.context.armed_object_type)
        self.assertEqual((), services.window_registry.keys())

    def test_end_active_session_blocks_pending_capture_review(self) -> None:
        services = build_app_services()
        services.session_editor_controller.open_document(SessionDocumentBuilder().build(session()))

        result = services.command_router.route(CommandId.END_ACTIVE_SESSION)

        self.assertEqual("blocked", result.status)
        self.assertIn("pending capture", result.message)
        self.assertIn("Save, retake, discard", result.next_ui_hint)
        self.assertIsNotNone(services.session_editor_controller.current_document)

    def test_end_active_session_blocks_dirty_editor_document(self) -> None:
        services = build_app_services()
        document = mark_metadata_edit(
            SessionDocumentBuilder().build(session_without_pending()),
            "dashboard",
            "name",
            "Edited",
        )
        services.session_editor_controller.open_document(document)

        result = services.command_router.route(CommandId.END_ACTIVE_SESSION)

        self.assertEqual("blocked", result.status)
        self.assertIn("unsaved editor edits", result.message)
        self.assertIn("Save or discard", result.next_ui_hint)
        self.assertIsNotNone(services.session_editor_controller.current_document)

    def test_blocked_end_active_session_is_recorded_as_warning_diagnostic(self) -> None:
        services = build_app_services()
        services.session_editor_controller.open_document(SessionDocumentBuilder().build(session()))

        result = services.command_router.route(CommandId.END_ACTIVE_SESSION)
        event = services.diagnostics_sink.recent(1)[0]

        self.assertEqual("blocked", result.status)
        self.assertEqual("warning", event.severity)
        self.assertEqual("CommandRouted", event.event_name)
        self.assertEqual("end_active_session", event.operation)

    def test_validate_session_hides_process_warnings_for_recipe_free_modes(self) -> None:
        services = build_app_services()
        source = replace(
            session_without_pending(),
            warnings=(
                WarningRecord(
                    id="process-warning",
                    message="Recipe missing",
                    source="process_context",
                    code="PROCESS_RECIPE_MISSING",
                ),
            ),
        )
        services.session_editor_controller.open_document(SessionDocumentBuilder().build(source))

        result = services.command_router.route(CommandId.VALIDATE_SESSION)

        self.assertEqual("success", result.status)
        self.assertEqual("Session document is valid.", result.message)
        self.assertEqual((), result.warning_ids)


if __name__ == "__main__":
    unittest.main()
