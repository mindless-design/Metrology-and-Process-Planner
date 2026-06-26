import tempfile
import unittest
import xml.etree.ElementTree as ET
from pathlib import Path

import tools.generate_visual_quality_gallery as gallery

from metrology_process_planner.persistence.paths import SessionPaths
from metrology_process_planner.testing.visual_quality import evaluate_image_path
from metrology_process_planner.ui.preview_widgets.presenter import PreviewPresenter
from metrology_process_planner.workflows.artifacts.visual_capture_generator import (
    generate_labeled_site_artifact,
)
from metrology_process_planner.workflows.editor.references import ArtifactRef
from tests.capture_metadata_pipeline_fixtures import line_feature_capture, session_with_capture

SVG_NS = "{http://www.w3.org/2000/svg}"

if __name__ == "__main__":
    unittest.main()


class ImagePipelineQualityTestsPart1(unittest.TestCase):
    def test_capture_svgs_embed_source_images_for_headless_renderers(self) -> None:
        gallery.main()

        root = Path("tests/output/visual_review_gallery")
        svg_path = root / "images/cap-001-site_image_labeled.svg"
        svg = ET.fromstring(svg_path.read_text(encoding="utf-8"))
        href = next(svg.iter(f"{SVG_NS}image")).get("href")

        self.assertTrue(str(href).startswith("data:image/png;base64,"))
        self.assertFalse((root / "images/images/cap-001.png").exists())
        self.assertEqual((), evaluate_image_path(svg_path, "labeled_site_image"))

    def test_point_annotation_label_is_kept_inside_canvas(self) -> None:
        gallery.main()

        svg_path = Path(
            "tests/output/visual_review_gallery/images/cap-001-point_annotation_image.svg"
        )
        svg = ET.fromstring(svg_path.read_text(encoding="utf-8"))
        text = next(
            item for item in svg.iter(f"{SVG_NS}text")
            if "".join(item.itertext()).strip() == "Film Stack Point"
        )

        self.assertGreaterEqual(float(text.get("x", "0")), 70.0)
        self.assertLessEqual(float(text.get("x", "0")), 954.0)
        self.assertGreaterEqual(float(text.get("y", "0")), 22.0)
        self.assertEqual((), evaluate_image_path(svg_path, "point_annotation_image"))

    def test_generated_capture_image_records_source_artifact_linkage(self) -> None:
        with tempfile.TemporaryDirectory() as folder:
            paths = SessionPaths.for_folder(Path(folder))
            image_dir = Path(folder) / "images"
            image_dir.mkdir()
            (image_dir / "cap-001.png").write_bytes(b"not-empty")
            session = session_with_capture(line_feature_capture())

            updated = generate_labeled_site_artifact(session, session.captures[0], paths)
            artifact_id = updated.captures[0].artifact_refs["site_image_labeled"]
            artifact = updated.artifacts[artifact_id]

        self.assertEqual(
            "capture-cap-001-site_image",
            artifact.extensions["source_image_artifact_id"],
        )
        self.assertEqual("images/cap-001.png", artifact.extensions["source_image_relative_path"])
        self.assertEqual("data_uri", artifact.extensions["source_image_embedding"])

    def test_visual_issue_detects_missing_svg_image_reference(self) -> None:
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder) / "bad.svg"
            path.write_text(
                '<svg xmlns="http://www.w3.org/2000/svg" width="100" height="100">'
                '<rect x="0" y="0" width="100" height="100" fill="#fff" />'
                '<image href="images/missing.png" x="0" y="0" width="100" height="100" />'
                "</svg>",
                encoding="utf-8",
            )

            issues = evaluate_image_path(path, "labeled_site_image")

        self.assertTrue(any(issue.category == "image_reference_missing" for issue in issues))

    def test_preview_presenter_keeps_missing_images_visible_and_repairable(self) -> None:
        preview = PreviewPresenter().from_artifacts(
            (
                ArtifactRef(
                    "site_image_labeled",
                    "images/missing.svg",
                    artifact_id="capture-cap-001-site_image_labeled",
                    status="missing",
                    message="Source image render failed.",
                    repair_action="regenerate_artifact",
                    repair_suggestion="Regenerate the visual artifact.",
                ),
            )
        )[0]

        self.assertEqual("missing", preview.status)
        self.assertIn("Source image render failed", preview.placeholder)
        self.assertIn("Regenerate the visual artifact", preview.placeholder)
        self.assertEqual("regenerate_artifact", preview.repair_action)
