import unittest

from metrology_process_planner.app.reporting_workbench_defaults import default_template_id
from metrology_process_planner.reporting import built_in_report_templates
from metrology_process_planner.reporting.templates import ReportTemplate


class ReportingWorkbenchTemplateTests(unittest.TestCase):
    def test_mode_sections_can_extend_template_without_exporter_changes(self) -> None:
        template = built_in_report_templates()["capture_catalog"]
        custom_template = ReportTemplate(
            template.template_id,
            template.name,
            template.required_sections,
            ("warning_summary", "appendix"),
        )

        sections = custom_template.ordered_sections(("warning_summary",))

        self.assertIn("warning_summary", sections)

    def test_default_templates_are_mode_specific(self) -> None:
        self.assertEqual("capture_catalog", default_template_id("simple_capture"))
        self.assertEqual("metrology_report", default_template_id("optical_metrology"))
        self.assertEqual("cad_review_report", default_template_id("cad_review"))
        self.assertEqual("process_flow_summary", default_template_id("process_flow_summary"))


if __name__ == "__main__":
    unittest.main()
