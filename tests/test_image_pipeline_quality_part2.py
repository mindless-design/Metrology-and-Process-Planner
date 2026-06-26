import json
import tempfile
import unittest
from pathlib import Path
from zipfile import ZipFile

import tools.generate_visual_quality_gallery as gallery
from tools.render_visual_quality_previews import render_visual_quality_previews

from metrology_process_planner.reporting.image_backend import ImagePackageBackend
from metrology_process_planner.reporting.models import (
    ArtifactSummary,
    ReportDocument,
    ReportMetadata,
)

SVG_NS = "{http://www.w3.org/2000/svg}"

if __name__ == "__main__":
    unittest.main()


class ImagePipelineQualityTestsPart2(unittest.TestCase):
    def test_report_image_bundle_contains_present_image_and_missing_placeholder(self) -> None:
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            image = root / "images/site.svg"
            image.parent.mkdir()
            image.write_text("<svg />", encoding="utf-8")
            document = ReportDocument(
                ReportMetadata("report-001", "Report", "default", "Default", "now", "s1", "Demo"),
                {},
                {},
                (),
                (),
                (
                    ArtifactSummary(
                        "present-image",
                        "Present",
                        "svg",
                        "site_image_labeled",
                        "present",
                        "images/site.svg",
                        "capture",
                        "cap-001",
                    ),
                    ArtifactSummary(
                        "missing-image",
                        "Missing",
                        "svg",
                        "site_image_labeled",
                        "missing",
                        "images/missing.svg",
                        "capture",
                        "cap-002",
                        placeholder=True,
                    ),
                ),
                (),
                {},
                (),
                {},
            )
            package_path = ImagePackageBackend(root).export(document, root / "bundle.zip")

            with ZipFile(package_path) as package:
                names = set(package.namelist())
                placeholder = package.read("placeholders/missing-image.txt").decode("utf-8")

        self.assertIn("images/site.svg", names)
        self.assertIn("placeholders/missing-image.txt", names)
        self.assertIn("Expected path: images/missing.svg", placeholder)

    def test_gallery_manifest_records_image_quality_contracts(self) -> None:
        gallery.main()

        manifest = json.loads(
            Path("tests/output/visual_review_gallery/manifest.json").read_text(encoding="utf-8")
        )

        self.assertTrue(all(item["status"] == "pass" for item in manifest))
        self.assertTrue(
            any(item["metadata_path"] for item in manifest if item["image_path"].endswith(".svg"))
        )

    def test_visual_preview_contact_sheet_is_repeatable(self) -> None:
        gallery.main()
        root = Path("tests/output/visual_review_gallery")

        contact_sheet = render_visual_quality_previews(root)

        self.assertTrue(contact_sheet.exists())
        self.assertTrue(
            (root / "rendered_previews/images__cap-001-line_annotation_image.svg.png").exists()
        )
        self.assertTrue(
            (root / "rendered_previews/process__physical_cross_section.svg.png").exists()
        )
