import json
import tempfile
import unittest
import zipfile
from dataclasses import replace
from pathlib import Path

from metrology_process_planner.domains.session import (
    ArtifactOwnerRef,
    ArtifactRecord,
    ArtifactStatus,
)
from metrology_process_planner.persistence.json_store import SessionJsonStore
from metrology_process_planner.reporting import (
    CsvReportBackend,
    ImagePackageBackend,
    PdfReportBackend,
    PowerPointReportBackend,
    ReadinessStatus,
    ReportExporter,
    ReportModelBuilder,
    ReportReadinessService,
    built_in_report_templates,
)
from metrology_process_planner.workflows.editor.builder import SessionDocumentBuilder

FIXTURES = Path(__file__).resolve().parent / "fixtures"


class ReportingPipelineTests(unittest.TestCase):
    def test_engineering_report_model_has_sections_and_numbering(self) -> None:
        document = _session_document()
        template = built_in_report_templates()["engineering_review"]

        report = ReportModelBuilder().build(document, template)

        self.assertEqual(
            (
                "cover_page",
                "revision_history",
                "session_summary",
                "capture_table",
                "capture_summary",
                "measurements",
            ),
            tuple(section.section_id for section in report.sections[:6]),
        )
        capture_section = report.sections[3]
        self.assertEqual(1, capture_section.tables[0].number)
        self.assertEqual("session-001", report.session_summary["session_id"])

    def test_readiness_reports_missing_required_artifacts(self) -> None:
        document = _session_document_with_missing_artifact()
        template = built_in_report_templates()["metrology_report"]

        readiness = ReportReadinessService().assess(document, template)

        self.assertEqual(ReadinessStatus.MISSING_REQUIRED_ARTIFACTS, readiness.status)
        self.assertTrue(any(item.code == "missing_artifact" for item in readiness.findings))

    def test_missing_artifacts_become_gallery_placeholders(self) -> None:
        document = _session_document_with_missing_artifact()
        template = built_in_report_templates()["metrology_report"]
        readiness = ReportReadinessService().assess(document, template)

        report = ReportModelBuilder().build(document, template, readiness.findings)

        gallery = next(
            section for section in report.sections if section.section_id == "artifact_gallery"
        )
        self.assertTrue(gallery.figures[0].placeholder)
        self.assertIn("Placeholder", gallery.figures[0].notes)

    def test_backends_write_pdf_pptx_csv_and_manifest(self) -> None:
        document = _session_document_with_missing_artifact()
        template = built_in_report_templates()["metrology_report"]
        report = ReportModelBuilder().build(document, template)
        exporter = ReportExporter(
            (
                PdfReportBackend(),
                PowerPointReportBackend(),
                CsvReportBackend(),
                ImagePackageBackend(),
            )
        )

        with tempfile.TemporaryDirectory() as temp_dir:
            exported = exporter.export(report, Path(temp_dir))
            manifest = json.loads(exported.manifest_path.read_text(encoding="utf-8"))

            pdf_bytes = exported.outputs["pdf"].read_bytes()
            self.assertTrue(pdf_bytes.startswith(b"%PDF-1.4"))
            self.assertIn(b"/Outlines", pdf_bytes)
            pptx_names = zipfile.ZipFile(exported.outputs["pptx"]).namelist()
            self.assertIn("ppt/slides/slide1.xml", pptx_names)
            slide_xml = zipfile.ZipFile(exported.outputs["pptx"]).read("ppt/slides/slide3.xml")
            self.assertIn(b"<a:tbl>", slide_xml)
            self.assertIn("cap-001", exported.outputs["csv"].read_text(encoding="utf-8"))
            image_names = zipfile.ZipFile(exported.outputs["images.zip"]).namelist()
            self.assertIn("placeholders/missing-image.txt", image_names)
            self.assertEqual(["missing-image"], manifest["artifact_list"])
            self.assertEqual(["pdf", "pptx", "csv", "images.zip"], manifest["export_formats"])

    def test_powerpoint_backend_embeds_present_images(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            image_path = Path(temp_dir) / "images" / "present.png"
            image_path.parent.mkdir()
            image_path.write_bytes(b"not-a-real-png-but-packaged")
            document = _session_document_with_artifact(
                ArtifactStatus.PRESENT,
                "present-image",
                "images/present.png",
            )
            template = built_in_report_templates()["metrology_report"]
            report = ReportModelBuilder().build(document, template)
            exporter = ReportExporter((PowerPointReportBackend(Path(temp_dir)),))

            exported = exporter.export(report, Path(temp_dir) / "out")
            names = zipfile.ZipFile(exported.outputs["pptx"]).namelist()
            rels = zipfile.ZipFile(exported.outputs["pptx"]).read(
                "ppt/slides/_rels/slide4.xml.rels"
            )

            self.assertIn("ppt/media/present-image.png", names)
            self.assertIn(b"relationships/image", rels)


def _session_document() -> object:
    session_path = FIXTURES / "sessions" / "simple_session" / "session.json"
    session = SessionJsonStore().load(session_path)
    return SessionDocumentBuilder().build(session)


def _session_document_with_missing_artifact() -> object:
    return _session_document_with_artifact(
        ArtifactStatus.MISSING,
        "missing-image",
        "images/missing.png",
    )


def _session_document_with_artifact(
    status: ArtifactStatus,
    artifact_id: str,
    relative_path: str,
) -> object:
    document = _session_document()
    artifact = ArtifactRecord(
        id=artifact_id,
        type="image",
        label="Report Image",
        relative_path=relative_path,
        status=status,
        owner=ArtifactOwnerRef("capture", "cap-001", "site_image"),
    )
    session = replace(document.session, artifacts={artifact.id: artifact})
    return SessionDocumentBuilder().build(session)


if __name__ == "__main__":
    unittest.main()
