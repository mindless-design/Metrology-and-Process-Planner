import tempfile
import unittest
from dataclasses import replace
from pathlib import Path

from metrology_process_planner.app.bootstrap import build_app_services
from metrology_process_planner.app.commands import CommandId
from metrology_process_planner.domains.session import (
    SessionMode,
)
from metrology_process_planner.persistence.paths import SessionPaths
from tests.editor_render_fixtures import session_without_pending

if __name__ == "__main__":
    unittest.main()


class DiagnosticsDashboardTestsPart1(unittest.TestCase):
    def test_dashboard_groups_recipe_free_rows_and_actions(self) -> None:
        services = build_app_services()
        with tempfile.TemporaryDirectory() as temp_dir:
            paths = SessionPaths.for_folder(Path(temp_dir) / "session")
            services.diagnostics_controller.set_active_session(session_without_pending(), paths)
            services.command_router.route(CommandId.OPEN_SETUP_GUIDE)

            result = services.diagnostics_controller.open_current()

        dashboard = result.window["dashboard"]
        sections = {section.section_id: section for section in dashboard.sections}
        session_rows = {row.label: row.value for row in sections["session"].rows}
        mode_policy_rows = {row.label: row.value for row in sections["mode_policy"].rows}
        report_rows = {row.label: row.value for row in sections["reports"].rows}
        activity_rows = {row.label: row.value for row in sections["activity"].rows}

        self.assertNotIn("process_report", sections)
        self.assertIn("session.json", session_rows["Active Session Path"])
        self.assertEqual("unknown", session_rows["Dirty State"])
        self.assertIn("simple_capture", mode_policy_rows["Loaded Mode Definition"])
        self.assertEqual("false", mode_policy_rows["Mode Process Aware"])
        self.assertEqual("false", mode_policy_rows["Recipe Required"])
        self.assertEqual("none", mode_policy_rows["Solver Operation"])
        self.assertEqual("false", mode_policy_rows["Process Context Visible"])
        self.assertEqual("not_required", mode_policy_rows["Setup State"])
        self.assertEqual("not requested", report_rows["Report Readiness"])
        self.assertEqual("open_setup_guide", activity_rows["Recent Commands"])
        self.assertIn("ExportDiagnosticsBundle", [action.action_id for action in dashboard.actions])

    def test_dashboard_keeps_process_rows_for_process_aware_modes(self) -> None:
        services = build_app_services()
        source = replace(
            session_without_pending(),
            mode=SessionMode.PROFILOMETRY_PLANNER,
        )
        services.diagnostics_controller.set_active_session(source)

        result = services.diagnostics_controller.open_current()

        sections = {section.section_id: section for section in result.window["dashboard"].sections}
        process_rows = {row.label: row.value for row in sections["process_report"].rows}
        self.assertNotIn("reports", sections)
        self.assertIn("Recipe Context", process_rows)
        self.assertIn("Solver Backend", process_rows)
        self.assertIn("Renderer Backend", process_rows)
        self.assertEqual("not requested", process_rows["Report Readiness"])
