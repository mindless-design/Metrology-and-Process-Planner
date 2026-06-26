import os
import unittest

from tools.klayout_runner import integration_tests_enabled, run_klayout_python_probe

from tests.klayout_process_common import report_from_stdout
from tests.klayout_process_scripts import (
    EXTRACT_INTERVALS_SCRIPT,
    LOAD_GDS_SCRIPT,
    RASTERIZE_SCRIPT,
    RENDER_SCENE_SCRIPT,
    SOLVER_SCRIPT,
)


@unittest.skipUnless(
    integration_tests_enabled(),
    "Set MPP_RUN_KLAYOUT_TESTS=1 to run real KLayout process regression tests.",
)
class KLayoutProcessRegressionTests(unittest.TestCase):
    def test_klayout_loads_synthetic_gds_named_cells_and_layers(self) -> None:
        result = run_klayout_python_probe(LOAD_GDS_SCRIPT)

        self.assertEqual(0, result.returncode, result.stderr)
        report = report_from_stdout(result.stdout)
        self.assertEqual("PROCESS_PLANNER_TESTCHIP", report["top_cell"])
        self.assertIn("conformal_liner_challenge", report["cell_names"])
        self.assertEqual(2, report["simple_line_space"]["POLY"])
        self.assertEqual(8, report["simple_line_space"]["METAL1"])
        self.assertEqual(12, report["grid_capture_test"]["GRID"])

    def test_klayout_extracts_mask_intervals_from_synthetic_gds(self) -> None:
        result = run_klayout_python_probe(EXTRACT_INTERVALS_SCRIPT)

        self.assertEqual(0, result.returncode, result.stderr)
        report = report_from_stdout(result.stdout)
        self.assertEqual([[12.0, 12.5], [13.2, 13.7]], report["line_space_first_two"])
        self.assertEqual([[40.0, 50.0]], report["trench"])
        self.assertEqual([[0.0, 1.0], [4.0, 12.0]], report["liner"])

    def test_klayout_extracted_masks_drive_solver_golden_summaries(self) -> None:
        result = run_klayout_python_probe(SOLVER_SCRIPT)

        self.assertEqual(0, result.returncode, result.stderr)
        report = report_from_stdout(result.stdout)
        self.assertEqual(report["expected_simple"], report["actual_simple"])
        self.assertEqual(report["expected_liner"], report["actual_liner"])
        self.assertEqual(report["expected_taper"], report["actual_taper"])

    def test_klayout_builds_render_scenes_matching_golden_summaries(self) -> None:
        result = run_klayout_python_probe(RENDER_SCENE_SCRIPT)

        self.assertEqual(0, result.returncode, result.stderr)
        report = report_from_stdout(result.stdout)
        self.assertEqual(report["expected_liner"], report["actual_liner"])
        self.assertEqual(report["expected_profile"], report["actual_profile"])
        self.assertEqual(report["expected_fib"], report["actual_fib"])

    def test_klayout_qt_rasterizes_cross_section_png(self) -> None:
        result = run_klayout_python_probe(RASTERIZE_SCRIPT, timeout_seconds=45)

        self.assertEqual(0, result.returncode, result.stderr)
        report = report_from_stdout(result.stdout)
        self.assertIn(report["status"], {"success", "warning"})
        self.assertTrue(report["png_exists"])
        self.assertTrue(report["png_size"] > 0)
        self.assertEqual("illustrative_process", report["render_mode_id"])


if __name__ == "__main__":
    os.environ.setdefault("MPP_RUN_KLAYOUT_TESTS", "1")
    unittest.main()
