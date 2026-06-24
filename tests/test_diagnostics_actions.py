import tempfile
import unittest
from pathlib import Path

from metrology_process_planner.app.bootstrap import build_app_services
from metrology_process_planner.app.commands import CommandId
from metrology_process_planner.persistence.paths import SessionPaths
from tests.editor_render_fixtures import session_without_pending


class DiagnosticsActionTests(unittest.TestCase):
    def test_diagnostics_actions_include_disabled_reasons(self) -> None:
        services = build_app_services()
        services.diagnostics_controller.set_active_session(session_without_pending())

        result = services.diagnostics_controller.open_current()
        actions = {action.action_id: action for action in result.window["actions"]}

        self.assertEqual(
            (
                "ExportDiagnosticsBundle",
                "CopyCommandTrace",
                "OpenSessionFolder",
                "ScanArtifacts",
                "ValidateSession",
                "ValidateModes",
            ),
            tuple(actions),
        )
        self.assertFalse(actions["CopyCommandTrace"].enabled)
        self.assertEqual(
            "No command or diagnostic events are available yet.",
            actions["CopyCommandTrace"].disabled_reason,
        )
        self.assertFalse(actions["OpenSessionFolder"].enabled)
        self.assertEqual(
            "No session folder is associated with diagnostics.",
            actions["OpenSessionFolder"].disabled_reason,
        )

    def test_diagnostics_actions_enable_trace_and_folder_handoffs(self) -> None:
        services = build_app_services()
        with tempfile.TemporaryDirectory() as temp_dir:
            paths = SessionPaths.for_folder(Path(temp_dir))
            services.diagnostics_controller.set_active_session(session_without_pending(), paths)
            services.command_router.route(CommandId.OPEN_SETUP_GUIDE)

            result = services.diagnostics_controller.open_current()

        actions = {action.action_id: action for action in result.window["actions"]}
        self.assertTrue(actions["CopyCommandTrace"].enabled)
        self.assertTrue(actions["OpenSessionFolder"].enabled)
        self.assertTrue(actions["ScanArtifacts"].enabled)


if __name__ == "__main__":
    unittest.main()
