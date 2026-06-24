import unittest
from pathlib import Path
from tempfile import TemporaryDirectory

from metrology_process_planner.app.bootstrap import build_app_services
from metrology_process_planner.app.commands import CommandId
from metrology_process_planner.persistence.paths import SessionPaths
from metrology_process_planner.workflows.editor import EditorAction, EditorActionType
from tests.editor_render_fixtures import session_without_pending


class SessionEditorExportCommandTests(unittest.TestCase):
    def test_export_csv_primary_action_routes_through_command_router(self) -> None:
        services = build_app_services()
        with TemporaryDirectory() as temp_dir:
            paths = SessionPaths.for_folder(Path(temp_dir))
            result = services.session_editor_controller.open_document(
                _document(),
                paths,
            )

            action = _primary_action(result.window, EditorActionType.EXPORT_CSV)
            result.window["on_primary_action"](action)

            routed = services.session_editor_controller.last_command_result
            self.assertIsNotNone(routed)
            self.assertEqual(CommandId.EXPORT_CSV, routed.command_id)
            self.assertEqual("success", routed.status)
            self.assertEqual(str(paths.capture_csv), routed.output_path)

    def test_open_output_folder_command_returns_path_handoff(self) -> None:
        services = build_app_services()
        with TemporaryDirectory() as temp_dir:
            paths = SessionPaths.for_folder(Path(temp_dir))
            services.session_editor_controller.open_document(_document(), paths)

            routed = services.command_router.route(CommandId.OPEN_OUTPUT_FOLDER)

        self.assertEqual("success", routed.status)
        self.assertEqual(str(paths.folder), routed.output_path)

    def test_open_output_folder_without_document_is_unavailable(self) -> None:
        services = build_app_services()

        routed = services.command_router.route(CommandId.OPEN_OUTPUT_FOLDER)

        self.assertEqual("unavailable", routed.status)
        self.assertIn("No active session editor document", routed.message)


def _document():
    from metrology_process_planner.workflows.editor import SessionDocumentBuilder

    return SessionDocumentBuilder().build(session_without_pending())


def _primary_action(window, action_type: EditorActionType) -> EditorAction:
    return next(action for action in window["primary_actions"] if action.action_type is action_type)


if __name__ == "__main__":
    unittest.main()
