import json
import tempfile
import unittest
from dataclasses import replace
from pathlib import Path

from PIL import Image

from metrology_process_planner.domains.session import (
    ArtifactOwnerRef,
    ArtifactRecord,
    ArtifactStatus,
)
from metrology_process_planner.reporting import (
    CsvReportBackend,
    ImagePackageBackend,
    PowerPointReportBackend,
    ReportExporter,
    ReportModelBuilder,
    built_in_report_templates,
)
from metrology_process_planner.workflows.editor.builder import SessionDocumentBuilder
from tests.editor_render_fixtures import session_without_pending
from tests.reporting_output_assertions import (
    assert_boxes_inside_slide,
    assert_no_box_overlaps,
    assert_pptx_relationships_resolve,
    placeholder_boxes,
    slide_boxes,
    slide_text,
)


class ReportingOutputQualityTests(unittest.TestCase):
    def test_powerpoint_slide_shapes_are_bounded_and_non_overlapping(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            report = _report_with_artifact(Path(temp_dir), ArtifactStatus.PRESENT)
            exported = ReportExporter((PowerPointReportBackend(Path(temp_dir)),)).export(
                report,
                Path(temp_dir) / "out",
            )

            assert_pptx_relationships_resolve(self, exported.outputs["pptx"])
            for slide_number in (1, 2, 3, 4):
                boxes = slide_boxes(exported.outputs["pptx"], slide_number)
                assert_boxes_inside_slide(self, boxes)
                assert_no_box_overlaps(self, boxes)

    def test_powerpoint_missing_image_has_visible_placeholder_metadata(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            report = _report_with_artifact(Path(temp_dir), ArtifactStatus.MISSING)
            exported = ReportExporter((PowerPointReportBackend(Path(temp_dir)),)).export(
                report,
                Path(temp_dir) / "out",
            )

            boxes = placeholder_boxes(exported.outputs["pptx"], 4)
            text = slide_text(exported.outputs["pptx"], 4)

            self.assertEqual(1, len(boxes))
            self.assertIn("Missing artifact: report-image", text)
            self.assertIn("Expected path: images/report.png", text)

    def test_powerpoint_two_image_gallery_uses_distinct_slots(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            folder = Path(temp_dir)
            report = _report_with_two_images(folder)
            exported = ReportExporter((PowerPointReportBackend(folder),)).export(
                report,
                folder / "out",
            )

            boxes = tuple(
                box
                for box in slide_boxes(exported.outputs["pptx"], 4)
                if box.name.startswith("Image")
            )

            self.assertEqual(2, len(boxes))
            assert_no_box_overlaps(self, boxes)

    def test_manifest_records_layout_placeholders_outputs_and_sections(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            report = _report_with_artifact(Path(temp_dir), ArtifactStatus.MISSING, "dark")
            exported = ReportExporter((PowerPointReportBackend(), CsvReportBackend())).export(
                report,
                Path(temp_dir) / "out",
            )

            manifest = json.loads(exported.manifest_path.read_text(encoding="utf-8"))

            self.assertIn("layout_metadata", manifest)
            self.assertEqual("dark", manifest["theme"])
            self.assertIn("artifact_gallery", manifest["included_sections"])
            self.assertEqual(["report-image"], manifest["missing_placeholder_artifacts"])
            self.assertIn("pptx", manifest["output_files"])
            self.assertIn("csv", manifest["output_files"])

    def test_csv_and_image_bundle_outputs_have_expected_quality_content(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            report = _report_with_artifact(Path(temp_dir), ArtifactStatus.MISSING)
            exported = ReportExporter(
                (CsvReportBackend(), ImagePackageBackend(Path(temp_dir)))
            ).export(report, Path(temp_dir) / "out")

            csv_text = exported.outputs["csv"].read_text(encoding="utf-8")
            measurement_csv = exported.outputs["csv"].with_name(
                exported.outputs["csv"].with_suffix("").name + ".measurements.csv"
            )

            self.assertIn("capture_id,label,role,status,measurements,artifacts", csv_text)
            self.assertIn("meas-001", measurement_csv.read_text(encoding="utf-8"))

def _report_with_artifact(folder: Path, status: ArtifactStatus, theme_id: str = "light"):
    if status is ArtifactStatus.PRESENT:
        image_path = folder / "images" / "report.png"
        image_path.parent.mkdir(parents=True)
        Image.new("RGB", (120, 80), (240, 240, 255)).save(image_path)
    document = SessionDocumentBuilder().build(
        replace(session_without_pending(), artifacts={"report-image": _artifact(status)})
    )
    template = built_in_report_templates()["metrology_report"]
    return ReportModelBuilder().build(document, template, theme_id=theme_id)


def _report_with_two_images(folder: Path):
    artifacts = {}
    for index in range(2):
        relative_path = f"images/report-{index}.png"
        image_path = folder / relative_path
        image_path.parent.mkdir(parents=True, exist_ok=True)
        Image.new("RGB", (120, 80), (220, 240, 255)).save(image_path)
        artifacts[f"report-image-{index}"] = _artifact_with_path(
            f"report-image-{index}",
            relative_path,
            ArtifactStatus.PRESENT,
        )
    document = SessionDocumentBuilder().build(
        replace(session_without_pending(), artifacts=artifacts)
    )
    return ReportModelBuilder().build(document, built_in_report_templates()["metrology_report"])


def _artifact(status: ArtifactStatus) -> ArtifactRecord:
    return _artifact_with_path("report-image", "images/report.png", status)


def _artifact_with_path(
    artifact_id: str,
    path: str,
    status: ArtifactStatus,
) -> ArtifactRecord:
    return ArtifactRecord(
        artifact_id,
        "image",
        "Report Image",
        path,
        ArtifactOwnerRef("capture", "cap-001", "site_image"),
        status=status,
    )
