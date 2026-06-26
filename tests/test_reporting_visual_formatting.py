import tempfile
import unittest
from dataclasses import replace
from pathlib import Path

from metrology_process_planner.domains.session import (
    ArtifactOwnerRef,
    ArtifactRecord,
    ArtifactStatus,
)
from metrology_process_planner.reporting import (
    PowerPointReportBackend,
    ReportExporter,
    ReportModelBuilder,
    built_in_report_templates,
)
from metrology_process_planner.reporting.themes import report_theme
from metrology_process_planner.workflows.editor.builder import SessionDocumentBuilder
from tests.editor_render_fixtures import session_without_pending
from tests.reporting_output_assertions import slide_boxes, slide_text, slide_xml


class ReportingVisualFormattingTests(unittest.TestCase):
    def test_dark_theme_applies_palette_to_native_powerpoint_shapes(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            exported = _export_pptx(Path(temp_dir), "dark")
            slide = slide_text(exported.outputs["pptx"], 4)
            xml = slide_xml(exported.outputs["pptx"], 4)
            theme = report_theme("dark")

            self.assertIn("Missing artifact: report-image", slide)
            self.assertIn(theme.background.encode("ascii"), xml)
            self.assertIn(theme.placeholder_fill.encode("ascii"), xml)
            self.assertIn(theme.text.encode("ascii"), xml)

    def test_powerpoint_adds_caption_context_and_footer_shapes(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            exported = _export_pptx(Path(temp_dir))
            names = {box.name for box in slide_boxes(exported.outputs["pptx"], 4)}
            text = slide_text(exported.outputs["pptx"], 4)

            self.assertIn("Figure Caption 60", names)
            self.assertIn("Section Context 3", names)
            self.assertIn("Footer 90", names)
            self.assertIn("Figure 1: Report Image | Artifact report-image", text)
            self.assertIn("Status: placeholder", text)

    def test_powerpoint_visual_tables_right_align_numeric_columns(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            exported = _export_pptx(Path(temp_dir))

            self.assertIn(b'algn="r"', slide_xml(exported.outputs["pptx"], 3))


def _export_pptx(folder: Path, theme_id: str = "light"):
    artifact = ArtifactRecord(
        "report-image",
        "image",
        "Report Image",
        "images/report.png",
        ArtifactOwnerRef("capture", "cap-001", "site_image"),
        status=ArtifactStatus.MISSING,
    )
    document = SessionDocumentBuilder().build(
        replace(session_without_pending(), artifacts={artifact.id: artifact})
    )
    report = ReportModelBuilder().build(
        document,
        built_in_report_templates()["metrology_report"],
        theme_id=theme_id,
    )
    return ReportExporter((PowerPointReportBackend(folder),)).export(report, folder / "out")


if __name__ == "__main__":
    unittest.main()
