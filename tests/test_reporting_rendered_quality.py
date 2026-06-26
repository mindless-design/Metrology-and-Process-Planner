import tempfile
import unittest
from dataclasses import replace
from importlib import util
from pathlib import Path

from metrology_process_planner.domains.session import (
    ArtifactOwnerRef,
    ArtifactRecord,
    ArtifactStatus,
)
from metrology_process_planner.reporting import PdfReportBackend, ReportExporter, ReportModelBuilder
from metrology_process_planner.reporting.templates import built_in_report_templates
from metrology_process_planner.workflows.editor.builder import SessionDocumentBuilder
from tests.editor_render_fixtures import session_without_pending


class ReportingRenderedQualityTests(unittest.TestCase):
    @unittest.skipUnless(util.find_spec("pypdf"), "pypdf dev dependency is not installed")
    def test_pdf_is_parseable_with_outline_and_expected_text(self) -> None:
        from pypdf import PdfReader

        with tempfile.TemporaryDirectory() as temp_dir:
            exported = _export_pdf(Path(temp_dir))

            reader = PdfReader(str(exported.outputs["pdf"]))
            text = "\n".join(page.extract_text() or "" for page in reader.pages)

            self.assertGreaterEqual(len(reader.pages), 2)
            self.assertTrue(reader.outline)
            self.assertIn("Metrology Report", reader.pages[0].extract_text())
            self.assertIn("Table of Contents", text)
            self.assertIn("Figure 1: Report Image | Artifact report-image", text)
            self.assertIn("Status: placeholder", text)

    @unittest.skipUnless(util.find_spec("pypdfium2"), "pypdfium2 is not installed")
    def test_pdf_rendered_pages_are_nonblank(self) -> None:
        import pypdfium2

        with tempfile.TemporaryDirectory() as temp_dir:
            exported = _export_pdf(Path(temp_dir))
            pdf = pypdfium2.PdfDocument(str(exported.outputs["pdf"]))
            bitmap = pdf[0].render(scale=1).to_pil()
            pdf.close()

            self.assertIsNotNone(bitmap.getbbox())

    def test_pdf_dark_theme_writes_background_color_commands(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            exported = _export_pdf(Path(temp_dir), "dark")
            payload = exported.outputs["pdf"].read_bytes()

            self.assertIn(b"0.067 0.094 0.153 rg", payload)


def _export_pdf(folder: Path, theme_id: str = "light"):
    report = ReportModelBuilder().build(
        _document(),
        built_in_report_templates()["metrology_report"],
        theme_id=theme_id,
    )
    return ReportExporter((PdfReportBackend(),)).export(report, folder / "out")


def _document():
    artifact = ArtifactRecord(
        "report-image",
        "image",
        "Report Image",
        "images/report.png",
        ArtifactOwnerRef("capture", "cap-001", "site_image"),
        status=ArtifactStatus.MISSING,
    )
    session = replace(session_without_pending(), artifacts={artifact.id: artifact})
    return SessionDocumentBuilder().build(session)


if __name__ == "__main__":
    unittest.main()
