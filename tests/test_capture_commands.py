import unittest
from dataclasses import replace

from metrology_process_planner.app.bootstrap import build_app_services
from metrology_process_planner.app.commands import CommandId
from metrology_process_planner.domains.session import CanvasVisualFlag
from metrology_process_planner.workflows.editor import SessionDocumentBuilder
from tests.editor_render_fixtures import session_without_pending


class CaptureCommandTests(unittest.TestCase):
    def test_start_box_capture_arms_editor_session_and_setup_mirror(self) -> None:
        services = build_app_services()
        source = session_without_pending()
        document = SessionDocumentBuilder().build(source)
        services.session_editor_controller.open_document(document)
        services.setup_guide_controller.set_active_session(source)

        result = services.command_router.route(CommandId.START_BOX_CAPTURE)
        editor_session = services.session_editor_controller.current_document.session
        setup_session = services.setup_guide_controller.active_session

        self.assertEqual("success", result.status)
        self.assertEqual("box_capture", editor_session.workflow.stage)
        self.assertEqual("site_box", editor_session.workflow.active_primitive)
        self.assertIsNotNone(setup_session)
        self.assertEqual("box_capture", setup_session.workflow.stage)

    def test_start_capture_aliases_box_capture(self) -> None:
        services = build_app_services()
        services.session_editor_controller.open_document(
            SessionDocumentBuilder().build(session_without_pending())
        )

        result = services.command_router.route(CommandId.START_CAPTURE)
        editor_session = services.session_editor_controller.current_document.session

        self.assertEqual("success", result.status)
        self.assertEqual("box_capture", editor_session.workflow.stage)
        self.assertEqual("site_box", editor_session.workflow.active_primitive)

    def test_start_line_capture_uses_selected_canvas_object_as_parent(self) -> None:
        services = build_app_services()
        source = session_without_pending()
        selected_canvas = replace(
            source.canvas_objects[0],
            visual_state=(CanvasVisualFlag.SELECTED,),
        )
        selected_source = replace(source, canvas_objects=(selected_canvas,))
        services.session_editor_controller.open_document(
            SessionDocumentBuilder().build(selected_source)
        )

        result = services.command_router.route(CommandId.START_LINE_CAPTURE)
        editor_session = services.session_editor_controller.current_document.session

        self.assertEqual("success", result.status)
        self.assertEqual("line_capture", editor_session.workflow.stage)
        self.assertEqual("measurement", editor_session.workflow.active_primitive)
        self.assertEqual("canvas-cap", services.capture_command_service.context.active_parent_id)

    def test_start_point_capture_sets_point_primitive_without_prompting(self) -> None:
        services = build_app_services()
        services.session_editor_controller.open_document(
            SessionDocumentBuilder().build(session_without_pending())
        )

        result = services.command_router.route(CommandId.START_POINT_CAPTURE)
        editor_session = services.session_editor_controller.current_document.session

        self.assertEqual("success", result.status)
        self.assertEqual("point_capture", editor_session.workflow.stage)
        self.assertEqual("point", editor_session.workflow.active_primitive)

    def test_cancel_capture_disarms_context_and_durable_workflow(self) -> None:
        services = build_app_services()
        services.session_editor_controller.open_document(
            SessionDocumentBuilder().build(session_without_pending())
        )
        services.command_router.route(CommandId.START_BOX_CAPTURE)

        result = services.command_router.route(CommandId.CANCEL_CAPTURE)
        editor_session = services.session_editor_controller.current_document.session

        self.assertEqual("success", result.status)
        self.assertFalse(editor_session.workflow.active)
        self.assertIsNone(services.capture_command_service.context.armed_object_type)

    def test_capture_command_without_active_session_returns_structured_error(self) -> None:
        services = build_app_services()

        result = services.command_router.route(CommandId.START_BOX_CAPTURE)

        self.assertEqual("error", result.status)
        self.assertIn("No active session", result.message)


if __name__ == "__main__":
    unittest.main()
