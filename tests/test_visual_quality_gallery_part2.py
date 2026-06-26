import json
import tempfile
import unittest
from pathlib import Path

import tools.generate_visual_quality_gallery as gallery

from metrology_process_planner.testing.visual_gallery_regression import compare_gallery_item
from metrology_process_planner.testing.visual_quality import (
    VisualManifestItem,
    evaluate_image_path,
    evaluate_visual_item,
    visual_status,
)

if __name__ == "__main__":
    unittest.main()


class VisualQualityGalleryTestsPart2(unittest.TestCase):
    def test_missing_required_legend_is_detected(self) -> None:
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            (root / "visual.svg").write_text(
                '<svg xmlns="http://www.w3.org/2000/svg" width="100" height="100">'
                '<rect x="0" y="0" width="100" height="100" fill="#fff" />'
                '<rect x="10" y="10" width="20" height="20" fill="#777" /></svg>',
                encoding="utf-8",
            )
            (root / "scene.json").write_text(
                json.dumps({"material_shapes": [{"material_id": "si"}], "legend": {}}),
                encoding="utf-8",
            )
            item = VisualManifestItem(
                "artifact",
                "physical_cross_section",
                "fixture",
                "mode",
                "profile",
                "visual.svg",
                "pending",
                metadata_path="scene.json",
            )

            issues = evaluate_visual_item(root, item)

        self.assertTrue(any(issue.category == "legend_missing" for issue in issues))

    def test_text_outside_canvas_is_detected(self) -> None:
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder) / "text.svg"
            path.write_text(
                '<svg xmlns="http://www.w3.org/2000/svg" width="100" height="100">'
                '<rect x="0" y="0" width="100" height="100" fill="#fff" />'
                '<text x="120" y="50">Outside</text></svg>',
                encoding="utf-8",
            )

            issues = evaluate_image_path(path, "labeled_site_image")

        self.assertTrue(any(issue.category == "text_clipped" for issue in issues))

    def test_visual_status_is_assigned_correctly(self) -> None:
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            item = VisualManifestItem(
                "artifact",
                "raw_site_image",
                "fixture",
                "mode",
                "profile",
                "missing.svg",
                "pending",
            )

            self.assertEqual("blocking", visual_status(evaluate_visual_item(root, item)))

    def test_site_overview_viewbox_text_is_not_false_positive_clipped(self) -> None:
        path = Path("tests/output/visual_review_gallery/images/cap-001-site_overview_image.svg")
        if not path.exists():
            gallery.main()

        issues = evaluate_image_path(path, "site_specific_overview_image")

        self.assertFalse(any(issue.category == "text_clipped" for issue in issues))

    def test_thin_liner_gets_callout_and_visible_legend_note(self) -> None:
        gallery.main()

        svg = Path("tests/output/visual_review_gallery/process/thin_conformal_liner.svg")
        scene = Path("tests/output/visual_review_gallery/process/thin_conformal_liner.scene.json")
        svg_text = svg.read_text(encoding="utf-8")
        issues = evaluate_visual_item(
            Path("tests/output/visual_review_gallery"),
            VisualManifestItem(
                "thin",
                "thin_conformal_liner",
                "fixture",
                "mode",
                "profile",
                "process/thin_conformal_liner.svg",
                "pending",
                metadata_path="process/thin_conformal_liner.scene.json",
            ),
        )

        self.assertIn("ALD Al2O3", svg_text)
        self.assertIn("Thin layers exaggerated", svg_text)
        self.assertIn("Materials", svg_text)
        self.assertTrue(scene.exists())
        self.assertEqual((), issues)

    def test_golden_mismatch_writes_debug_artifact(self) -> None:
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            (root / "scene.json").write_text(
                json.dumps(
                    {
                        "render_mode_id": "demo",
                        "material_shapes": [{"material_id": "oxide", "exaggerated_flag": False}],
                        "labels": [],
                        "warnings": [],
                        "compression_metadata": {"enabled": False, "affected_materials": []},
                    }
                ),
                encoding="utf-8",
            )
            golden_root = root / "golden"
            golden_root.mkdir()
            (golden_root / "fixture.profile.expected.json").write_text(
                json.dumps({"shape_count": 99}),
                encoding="utf-8",
            )
            item = VisualManifestItem(
                "artifact:demo",
                "physical_cross_section",
                "fixture",
                "demo",
                "profile",
                "visual.svg",
                "pending",
                metadata_path="scene.json",
            )

            result = compare_gallery_item(root, item, golden_root, root / "debug")

        self.assertEqual("mismatch", result.status)
        self.assertTrue(result.debug_path.endswith("artifact_demo.visual-gallery-comparison.json"))
