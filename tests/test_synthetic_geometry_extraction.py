import json
import unittest
from pathlib import Path

from tests.synthetic_process_lab import (
    GDS_ROOT,
    cutline_sample,
    extract_structure,
    layer_coverage,
    point_sample,
    require_layer,
)


class SyntheticGeometryExtractionTests(unittest.TestCase):
    def test_generated_gds_and_manifest_exist(self) -> None:
        self.assertTrue((GDS_ROOT / "process_planner_testchip.gds").exists())
        manifest = json.loads((GDS_ROOT / "process_planner_testchip.geometry.json").read_text())

        self.assertEqual("PROCESS_PLANNER_TESTCHIP", manifest["top_cell"])
        self.assertEqual("um", manifest["units"])
        self.assertEqual(15, len(manifest["layers"]))

    def test_known_layer_is_found(self) -> None:
        snapshot = extract_structure("simple_line_space")

        self.assertIn("POLY", snapshot.layer_names())
        self.assertFalse(require_layer(snapshot, "POLY"))

    def test_missing_layer_creates_warning(self) -> None:
        snapshot = extract_structure("simple_line_space")
        warnings = require_layer(snapshot, "DOES_NOT_EXIST")

        self.assertEqual("GEOMETRY_LAYER_MISSING", warnings[0].code)

    def test_known_point_is_inside_expected_mask(self) -> None:
        sample = point_sample("point_stack_ellipsometry", 50.0, 64.0)

        self.assertEqual(("METAL1", "METAL2"), sample.layers)
        self.assertIn("overlap_point", sample.rectangles)

    def test_known_point_is_outside_expected_mask(self) -> None:
        sample = point_sample("point_stack_ellipsometry", 75.0, 64.0)

        self.assertEqual((), sample.layers)

    def test_cutline_across_line_space_creates_expected_intervals(self) -> None:
        sample = cutline_sample("simple_line_space", 6.0, "METAL1")

        self.assertEqual(8, len(sample.intervals))
        self.assertEqual((12.0, 12.5), (sample.intervals[0].x_min, sample.intervals[0].x_max))

    def test_cutline_across_trench_creates_expected_opening_intervals(self) -> None:
        sample = cutline_sample("trench_via_etch", 7.5, "TRENCH")

        self.assertEqual(
            ("narrow_trench",),
            tuple(interval.source_rect for interval in sample.intervals),
        )

    def test_roi_extraction_includes_expected_polygons_and_layers(self) -> None:
        snapshot = extract_structure("cmp_planarization_density", roi=(58.0, 29.0, 66.5, 36.5))

        self.assertEqual(("CMP_DENSITY",), snapshot.layer_names())
        self.assertGreaterEqual(len(snapshot.rectangles), 10)

    def test_layer_coverage_summary_is_deterministic(self) -> None:
        first = layer_coverage(extract_structure("label_stress_test"))
        second = layer_coverage(extract_structure("label_stress_test"))

        self.assertEqual(first, second)
        self.assertEqual({"LABEL_STRESS_TEST": 94.5}, first)

    def test_generator_is_source_of_truth_for_binary_fixture(self) -> None:
        generator = Path("tests/fixtures/gds/generate_process_planner_testchip.py")

        self.assertTrue(generator.exists())


if __name__ == "__main__":
    unittest.main()
