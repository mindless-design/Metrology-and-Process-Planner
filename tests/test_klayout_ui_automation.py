import os
import unittest

from tools.klayout_ui_robot import main_window_snapshot_script, menu_registration_script
from tools.klayout_ui_runner import run_klayout_ui_probe, ui_tests_enabled


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
        self.assertEqual(5, result.report.get("command_count"))
        self.assertTrue(all(result.report.get("menu_path_validity", {}).values()))

    def test_real_klayout_main_window_snapshot(self) -> None:
        result = run_klayout_ui_probe(main_window_snapshot_script())

        self.assertFalse(result.timed_out, result.stderr)
        self.assertEqual(0, result.returncode, result.stderr)
        self.assertTrue(result.report.get("ok"), result.report)
        self.assertTrue(result.report.get("has_menu"), result.report)
        self.assertTrue(result.report.get("has_current_view"), result.report)


if __name__ == "__main__":
    os.environ.setdefault("MPP_RUN_KLAYOUT_UI_TESTS", "1")
    unittest.main()
