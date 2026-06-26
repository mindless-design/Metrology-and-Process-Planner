import os
import unittest

from tools.klayout_ui_capture_robot import capture_surface_contract_script
from tools.klayout_ui_non_process_robot import non_process_editor_surface_script
from tools.klayout_ui_robot import (
    main_window_snapshot_script,
    menu_registration_script,
    modeless_command_surface_script,
)
from tools.klayout_ui_runner import run_klayout_ui_probe, ui_tests_enabled
from tools.klayout_ui_setup_robot import non_process_setup_guide_surface_script

from metrology_process_planner.app.commands import MENU_COMMANDS
from metrology_process_planner.domains.session import SessionMode


@unittest.skipUnless(
    ui_tests_enabled(),
    "Set MPP_RUN_KLAYOUT_UI_TESTS=1 to run real KLayout GUI automation tests.",
)
class KLayoutUiAutomationTests(unittest.TestCase):
    def test_real_klayout_menu_registration(self) -> None:
        result = run_klayout_ui_probe(menu_registration_script())

        self.assertFalse(result.timed_out, result.stderr)
        self.assertEqual(0, result.returncode, result.stderr)
        self.assertTrue(result.report.get("ok"), result.report)
        self.assertTrue(result.report.get("menu_valid"), result.report)
        self.assertEqual(len(MENU_COMMANDS), result.report.get("command_count"))
        self.assertTrue(all(result.report.get("menu_path_validity", {}).values()))

    def test_real_klayout_main_window_snapshot(self) -> None:
        result = run_klayout_ui_probe(main_window_snapshot_script())

        self.assertFalse(result.timed_out, result.stderr)
        self.assertEqual(0, result.returncode, result.stderr)
        self.assertTrue(result.report.get("ok"), result.report)
        self.assertTrue(result.report.get("has_menu"), result.report)
        self.assertTrue(result.report.get("has_current_view"), result.report)

    def test_real_klayout_modeless_command_surfaces(self) -> None:
        result = run_klayout_ui_probe(modeless_command_surface_script())

        self.assertFalse(result.timed_out, result.stderr)
        self.assertEqual(0, result.returncode, result.stderr)
        self.assertTrue(result.report.get("ok"), result.report)
        routed = result.report.get("routed", {})
        self.assertEqual("success", routed["open_session_editor"]["status"])
        self.assertEqual("success", routed["open_setup_guide"]["status"])
        self.assertEqual("success", routed["open_recipe_editor"]["status"])
        self.assertEqual("success", routed["open_diagnostics"]["status"])
        self.assertEqual("unavailable", routed["open_reporting_workbench"]["status"])
        self.assertGreaterEqual(result.report.get("diagnostic_events", 0), 5)
        self.assertTrue(result.report.get("window_keys"), result.report)

    def test_real_klayout_capture_surface_contracts(self) -> None:
        result = run_klayout_ui_probe(capture_surface_contract_script())

        self.assertFalse(result.timed_out, result.stderr)
        self.assertEqual(0, result.returncode, result.stderr)
        self.assertTrue(result.report.get("ok"), result.report)
        self.assertFalse(result.report.get("box_ignored"), result.report)
        self.assertTrue(result.report.get("box_released"), result.report)
        self.assertEqual("box", result.report.get("box_pending_kind"))
        self.assertTrue(result.report.get("measurement_released"), result.report)
        self.assertEqual("meas-001", result.report.get("measurement_id"))
        self.assertTrue(result.report.get("standalone_line_released"), result.report)
        self.assertEqual("line", result.report.get("standalone_line_kind"))
        self.assertTrue(result.report.get("point_released"), result.report)
        self.assertEqual("point", result.report.get("point_kind"))
        counts = result.report.get("overlay_command_counts", {})
        self.assertTrue(all(count > 0 for count in counts.values()), result.report)

    def test_real_klayout_non_process_editor_surfaces_hide_process_ui(self) -> None:
        result = run_klayout_ui_probe(non_process_editor_surface_script())

        self.assertFalse(result.timed_out, result.stderr)
        self.assertEqual(0, result.returncode, result.stderr)
        self.assertTrue(result.report.get("ok"), result.report)
        reports = result.report.get("mode_reports", {})
        self.assertIn(SessionMode.SIMPLE_CAPTURE.value, reports)
        for mode_report in reports.values():
            self.assertNotIn("Process Context", mode_report["header_keys"])
            self.assertNotIn("Cross Sections", mode_report["navigator_groups"])
            self.assertFalse(
                {
                    "attach_recipe",
                    "detach_recipe",
                    "validate_process_context",
                    "regenerate_process_output",
                }
                & set(mode_report["action_types"]),
                mode_report,
            )

    def test_real_klayout_non_process_setup_guides_hide_process_ui(self) -> None:
        result = run_klayout_ui_probe(non_process_setup_guide_surface_script())

        self.assertFalse(result.timed_out, result.stderr)
        self.assertEqual(0, result.returncode, result.stderr)
        self.assertTrue(result.report.get("ok"), result.report)
        reports = result.report.get("mode_reports", {})
        optical = reports[SessionMode.OPTICAL_METROLOGY.value]
        cdsem = reports[SessionMode.CDSEM_MEASUREMENT.value]
        self.assertIn("optical_alignment", optical["card_stage_ids"])
        self.assertIn("ready_for_capture", optical["card_stage_ids"])
        self.assertIn("optical_alignment", cdsem["card_stage_ids"])
        self.assertIn("sem_alignment", cdsem["card_stage_ids"])
        for mode_report in reports.values():
            labels = (
                mode_report["card_titles"]
                + mode_report["primary_action_labels"]
                + mode_report["secondary_action_labels"]
                + mode_report["footer_action_labels"]
                + [mode_report["status"]]
            )
            self.assertFalse(any("Recipe" in label for label in labels), mode_report)
            self.assertFalse(any("Process Context" in label for label in labels), mode_report)


if __name__ == "__main__":
    os.environ.setdefault("MPP_RUN_KLAYOUT_UI_TESTS", "1")
    unittest.main()
