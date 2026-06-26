import unittest
from dataclasses import replace

from metrology_process_planner.domains.session import (
    ArtifactOwnerRef,
    ArtifactRecord,
    ArtifactRepairMetadata,
    ArtifactStatus,
    ModeDefinition,
    ModeRegistry,
    WarningRecord,
)
from metrology_process_planner.reporting import ReportModelBuilder
from metrology_process_planner.reporting.readiness import (
    ReadinessStatus,
    ReportReadinessService,
)
from metrology_process_planner.reporting.requests import ReportRequest
from metrology_process_planner.reporting.templates import built_in_report_templates
from metrology_process_planner.workflows.editor.builder import SessionDocumentBuilder
from tests.editor_render_fixtures import session_without_pending


def _document_with_hidden_process_artifact(
    artifact_type: str = "process_output",
    repair: ArtifactRepairMetadata | None = None,
    owner: ArtifactOwnerRef | None = None,
):
    source = session_without_pending()
    if repair is None:
        repair = _process_repair()
    process_artifact = ArtifactRecord(
        "legacy-process-output",
        artifact_type,
        "Legacy Stack Image",
        "process_outputs/legacy-stack.png",
        owner or ArtifactOwnerRef("process_output", "legacy-output", "stack_image"),
        status=ArtifactStatus.MISSING,
        repair=repair,
    )
    artifacts = dict(source.artifacts or {})
    artifacts[process_artifact.id] = process_artifact
    capture = replace(
        source.captures[0],
        artifact_refs={
            **dict(source.captures[0].artifact_refs or {}),
            "stack_image": process_artifact.id,
        },
    )
    document = SessionDocumentBuilder().build(
        replace(source, captures=(capture,), artifacts=artifacts)
    )
    return document, process_artifact

def _process_repair() -> ArtifactRepairMetadata:
    return ArtifactRepairMetadata(
        repair_action="regenerate_process_output",
        repair_suggestion="Regenerate process output.",
        requires_recipe=True,
        requires_solver=True,
    )

def _recipe_free_registry_for(mode_id: str) -> ModeRegistry:
    return ModeRegistry((ModeDefinition(mode_id, "Recipe Free Override"),))

if __name__ == "__main__":
    unittest.main()


class ReportingNonProcessVisibilityTestsPart1(unittest.TestCase):
    def test_recipe_free_report_hides_process_context_warnings(self) -> None:
        session = replace(
            session_without_pending(),
            warnings=(
                WarningRecord(
                    "process-warning",
                    "Recipe missing",
                    source="process_context",
                    code="PROCESS_RECIPE_FILE_NOT_FOUND",
                ),
                WarningRecord("artifact-warning", "Artifact missing", code="ARTIFACT_MISSING"),
            ),
        )
        document = SessionDocumentBuilder().build(session)
        template = built_in_report_templates()["executive_summary"]

        report = ReportModelBuilder().build(document, template)

        self.assertEqual(["artifact-warning"], [warning.warning_id for warning in report.warnings])
        self.assertEqual(1, report.session_summary["warnings"])
        self.assertEqual({}, report.process_context_summary)
        warning_section = next(
            section for section in report.sections if section.section_id == "warning_summary"
        )
        warning_rows = warning_section.tables[0].rows
        self.assertEqual(["artifact-warning"], [row["warning_id"] for row in warning_rows])

    def test_recipe_free_report_hides_process_output_artifacts(self) -> None:
        document, process_artifact = _document_with_hidden_process_artifact()
        template = built_in_report_templates()["capture_catalog"]

        report = ReportModelBuilder().build(document, template)

        self.assertEqual(1, report.session_summary["artifacts"])
        self.assertNotIn(process_artifact.id, report.captures[0].artifact_ids)
        self.assertNotIn(
            "legacy-process-output",
            {artifact.artifact_id for artifact in report.artifacts},
        )
        gallery = next(
            section for section in report.sections if section.section_id == "artifact_gallery"
        )
        self.assertNotIn(
            "legacy-process-output",
            {figure.artifact_id for figure in gallery.figures},
        )
        capture_table = next(
            section for section in report.sections if section.section_id == "capture_table"
        )
        self.assertEqual(0, capture_table.tables[0].rows[0]["artifacts"])

    def test_recipe_free_report_hides_generic_images_with_process_roles(self) -> None:
        document, process_artifact = _document_with_hidden_process_artifact(
            artifact_type="image",
            repair=ArtifactRepairMetadata(),
            owner=ArtifactOwnerRef("capture", "cap-001", "stack_image"),
        )
        template = built_in_report_templates()["capture_catalog"]

        report = ReportModelBuilder().build(document, template)

        self.assertNotIn(process_artifact.id, report.captures[0].artifact_ids)
        self.assertNotIn(
            process_artifact.id,
            {artifact.artifact_id for artifact in report.artifacts},
        )

    def test_recipe_free_report_readiness_hides_process_output_artifacts(self) -> None:
        document, _process_artifact = _document_with_hidden_process_artifact()

        readiness = ReportReadinessService().assess_request(
            document,
            ReportRequest(document.session.id, "capture_catalog"),
        )
        self.assertNotEqual(ReadinessStatus.MISSING_REQUIRED_ARTIFACTS, readiness.status)
        self.assertNotIn("legacy-process-output", readiness.missing_required_artifacts)

    def test_recipe_free_report_omits_requested_process_sections(self) -> None:
        document = SessionDocumentBuilder().build(session_without_pending())
        template = built_in_report_templates()["fib_planning_package"]

        report = ReportModelBuilder().build(
            document,
            template,
            requested_sections=("cross_section_gallery",),
        )

        self.assertNotIn(
            "cross_section_gallery",
            {section.section_id for section in report.sections},
        )
