import tempfile
import unittest
from dataclasses import replace
from pathlib import Path

from metrology_process_planner.domains.session import ArtifactStatus, SessionMode
from metrology_process_planner.reporting import (
    PlaceholderPolicy,
    ReadinessStatus,
    ReportGenerationService,
    ReportReadinessService,
    ReportRequest,
)
from metrology_process_planner.workflows.editor.builder import SessionDocumentBuilder
from metrology_process_planner.workflows.grid_measurement import create_grid_dataset
from tests.process_context_fixtures import session as process_session
from tests.reporting_workbench_fixtures import document as base_document
from tests.reporting_workbench_fixtures import document_with_artifact
from tests.test_grid_measurement_workflow import _session as grid_session


class ReportingReadinessTests(unittest.TestCase):
    def test_placeholder_policy_allows_missing_required_artifact(self) -> None:
        document = document_with_artifact(ArtifactStatus.MISSING)
        request = ReportRequest(
            document.session.id,
            "metrology_report",
            placeholder_policy=PlaceholderPolicy.PLACEHOLDER_REQUIRED,
        )

        readiness = ReportReadinessService().assess_request(document, request)

        self.assertEqual(ReadinessStatus.READY_WITH_WARNINGS, readiness.status)
        self.assertTrue(readiness.can_generate())
        self.assertIn("missing-image", readiness.missing_required_artifacts)

    def test_strict_placeholder_policy_blocks_missing_required_artifact(self) -> None:
        document = document_with_artifact(ArtifactStatus.MISSING)
        request = ReportRequest(
            document.session.id,
            "metrology_report",
            placeholder_policy=PlaceholderPolicy.STRICT,
        )

        readiness = ReportReadinessService().assess_request(document, request)

        self.assertEqual(ReadinessStatus.VALIDATION_FAILED, readiness.status)
        self.assertFalse(readiness.can_generate())

    def test_unsupported_template_is_rejected_cleanly(self) -> None:
        document = base_document()
        request = ReportRequest(document.session.id, "does_not_exist")

        readiness = ReportReadinessService().assess_request(document, request)

        self.assertEqual(ReadinessStatus.EXPORT_BLOCKED, readiness.status)
        self.assertEqual("unsupported_template", readiness.blocking_issues[0].code)

    def test_recipe_free_report_ignores_process_context_section_selection(self) -> None:
        document = base_document()
        request = ReportRequest(
            document.session.id,
            "engineering_review",
            selected_sections=("process_context",),
        )

        readiness = ReportReadinessService().assess_request(document, request)

        self.assertNotIn(
            "missing_process_context",
            {item.code for item in readiness.findings},
        )
        self.assertTrue(readiness.can_generate())

    def test_recipe_free_report_templates_accept_builtin_mode_aliases(self) -> None:
        aliases = (
            (SessionMode.SIMPLE_LABELED_CAPTURE, "metrology_report"),
            (SessionMode.CAD_REVIEW_CAPTURE, "cad_review_report"),
            (SessionMode.CDSEM_CAPTURE, "metrology_report"),
        )

        for mode, template_id in aliases:
            with self.subTest(mode=mode.value, template=template_id):
                source = replace(base_document().session, mode=mode)
                document = SessionDocumentBuilder().build(source)

                readiness = ReportReadinessService().assess_request(
                    document,
                    ReportRequest(document.session.id, template_id),
                )

                self.assertNotIn(
                    "unsupported_template",
                    {item.code for item in readiness.blocking_issues},
                )

    def test_process_aware_report_still_requires_process_context(self) -> None:
        document = SessionDocumentBuilder().build(process_session())
        request = ReportRequest(document.session.id, "process_review")

        readiness = ReportReadinessService().assess_request(document, request)

        self.assertEqual(ReadinessStatus.VALIDATION_FAILED, readiness.status)
        self.assertIn(
            "missing_process_context",
            {item.code for item in readiness.blocking_issues},
        )

    def test_generated_reports_are_registered_as_session_artifacts(self) -> None:
        document = document_with_artifact(ArtifactStatus.MISSING)
        request = ReportRequest(document.session.id, "metrology_report", output_formats=("pptx",))

        with tempfile.TemporaryDirectory() as temp_dir:
            result = ReportGenerationService().generate(document, request, Path(temp_dir))

        self.assertIsNotNone(result.updated_session)
        assert result.updated_session is not None
        assert result.updated_session.artifacts is not None
        artifact_types = {item.type for item in result.updated_session.artifacts.values()}
        self.assertIn("powerpoint_deck", artifact_types)
        self.assertIn("report_manifest", artifact_types)
        self.assertTrue(result.updated_session.reports)

    def test_stale_report_dependencies_affect_readiness(self) -> None:
        document = document_with_artifact(ArtifactStatus.STALE)
        request = ReportRequest(document.session.id, "metrology_report")

        readiness = ReportReadinessService().assess_request(document, request)

        self.assertEqual(ReadinessStatus.STALE_OUTPUTS, readiness.status)
        self.assertIn("missing-image", readiness.stale_artifacts)

    def test_placeholder_grid_overview_warns_without_blocking_report(self) -> None:
        session = create_grid_dataset(grid_session(), "cap-a", "cap-b", 2, 2)
        document = SessionDocumentBuilder().build(session)

        readiness = ReportReadinessService().assess_request(
            document,
            ReportRequest(document.session.id, "capture_catalog"),
        )

        self.assertEqual(ReadinessStatus.READY_WITH_WARNINGS, readiness.status)
        self.assertTrue(readiness.can_generate())
        self.assertIn("placeholder_artifact", {item.code for item in readiness.warnings})


if __name__ == "__main__":
    unittest.main()
