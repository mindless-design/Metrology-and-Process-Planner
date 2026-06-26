import json
import tempfile
import unittest
from pathlib import Path

import tools.generate_visual_quality_gallery as gallery

from metrology_process_planner.testing.visual_quality import (
    VisualManifestItem,
    evaluate_image_path,
    evaluate_visual_item,
    overlapping_label_pairs,
    selected_line_issue,
    selected_point_issue,
    visual_status,
)

if __name__ == "__main__":
    unittest.main()


class VisualQualityGalleryTestsPart1(unittest.TestCase):
    def test_visual_review_gallery_generates_manifest(self) -> None:
        gallery.main()

        output = Path("tests/output/visual_review_gallery")
        manifest = json.loads((output / "manifest.json").read_text(encoding="utf-8"))

        self.assertTrue((output / "index.html").exists())
        self.assertTrue((output / "visual_issues.json").exists())
        self.assertGreaterEqual(len(manifest), 10)
        self.assertTrue(all(item["status"] for item in manifest))
        required = {
            "visual_type",
            "source_artifact_id",
            "capture_id",
            "status",
            "warnings",
            "output_path",
            "metadata",
            "comparison_status",
        }
        self.assertTrue(all(required.issubset(item) for item in manifest))

    def test_all_expected_visual_categories_appear(self) -> None:
        gallery.main()

        manifest = json.loads(
            Path("tests/output/visual_review_gallery/manifest.json").read_text(encoding="utf-8")
        )
        visual_types = {item["visual_type"] for item in manifest}

        self.assertIn("raw_site_image", visual_types)
        self.assertIn("labeled_site_image", visual_types)
        self.assertIn("site_specific_overview_image", visual_types)
        self.assertIn("line_annotation_image", visual_types)
        self.assertIn("point_annotation_image", visual_types)
        self.assertIn("measurement_annotation_image", visual_types)
        self.assertIn("profilometry_surface_profile", visual_types)
        self.assertIn("physical_cross_section", visual_types)
        self.assertIn("fib_full_stack_compressed", visual_types)
        self.assertIn("process_flow_frame", visual_types)

    def test_manifest_records_golden_comparisons_and_warning_metadata(self) -> None:
        gallery.main()

        output = Path("tests/output/visual_review_gallery")
        manifest = json.loads((output / "manifest.json").read_text(encoding="utf-8"))
        by_type = {item["visual_type"]: item for item in manifest}

        physical = by_type["physical_cross_section"]
        liner = by_type["thin_conformal_liner"]
        labeled = by_type["labeled_site_image"]

        self.assertEqual("matched", physical["comparison_status"])
        self.assertTrue((output / physical["comparison_path"]).exists())
        self.assertIn("RENDER_THIN_LAYER_EXAGGERATED", liner["warnings"])
        self.assertEqual("cap-001", labeled["capture_id"])
        self.assertTrue((output / labeled["metadata_path"]).exists())

    def test_missing_visual_generation_produces_issue_record(self) -> None:
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            item = VisualManifestItem(
                "missing",
                "raw_site_image",
                "fixture",
                "mode",
                "profile",
                "missing.svg",
                "pending",
            )

            issues = evaluate_visual_item(root, item)

        self.assertEqual("missing_artifact", issues[0].category)
        self.assertEqual("blocking", visual_status(issues))

    def test_blank_image_is_detected(self) -> None:
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder) / "blank.svg"
            path.write_text(
                '<svg xmlns="http://www.w3.org/2000/svg" width="100" height="100">'
                '<rect x="0" y="0" width="100" height="100" fill="#fff" /></svg>',
                encoding="utf-8",
            )

            issues = evaluate_image_path(path, "raw_site_image")

        self.assertTrue(any(issue.category == "blank_image" for issue in issues))

    def test_label_overlap_is_detected(self) -> None:
        pairs = overlapping_label_pairs(
            (
                {"label_id": "a", "bounding_box": (0, 0, 20, 20)},
                {"label_id": "b", "bounding_box": (10, 10, 20, 20)},
            )
        )

        self.assertEqual((("a", "b"),), pairs)

    def test_selected_line_outside_bounds_is_detected(self) -> None:
        issue = selected_line_issue(100, 100, (120, 120), (130, 130))

        self.assertIsNotNone(issue)
        self.assertEqual("selected_feature_missing", issue.category)

    def test_selected_point_outside_bounds_is_detected(self) -> None:
        issue = selected_point_issue(100, 100, (-1, 50))

        self.assertIsNotNone(issue)
        self.assertEqual("selected_feature_missing", issue.category)
