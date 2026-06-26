import unittest
from dataclasses import replace

from metrology_process_planner.domains.session import (
    ArtifactOwnerRef,
    ArtifactRecord,
    ArtifactRepairMetadata,
    ArtifactStatus,
    ModeDefinition,
    ModeRegistry,
    ProcessContext,
    SessionMode,
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


class ReportingNonProcessVisibilityTestsPart2(unittest.TestCase):
    def test_loaded_recipe_free_registry_hides_process_context_for_process_named_mode(
        self,
    ) -> None:
        registry = _recipe_free_registry_for(SessionMode.PROFILOMETRY_PLANNER.value)
        session = replace(
            session_without_pending(),
            mode=SessionMode.PROFILOMETRY_PLANNER,
            process_context=ProcessContext(
                recipe_reference="legacy-recipe.json",
                recipe_id="legacy-recipe",
                recipe_name="Legacy Recipe",
            ),
            warnings=(
                WarningRecord(
                    "process-warning",
                    "Recipe attached but hidden",
                    source="process_context",
                    code="PROCESS_CONTEXT_ATTACHED",
                ),
            ),
        )
        document = SessionDocumentBuilder(mode_registry=registry).build(session)
        template = built_in_report_templates()["process_review"]

        report = ReportModelBuilder(mode_registry=registry).build(document, template)

        self.assertEqual({}, report.process_context_summary)
        self.assertNotIn("process_context", {section.section_id for section in report.sections})
        self.assertEqual((), report.warnings)
        self.assertEqual(0, report.session_summary["warnings"])

    def test_loaded_recipe_free_registry_prevents_process_context_readiness_block(
        self,
    ) -> None:
        registry = _recipe_free_registry_for(SessionMode.PROFILOMETRY_PLANNER.value)
        session = replace(
            session_without_pending(),
            mode=SessionMode.PROFILOMETRY_PLANNER,
            process_context=ProcessContext(),
        )
        document = SessionDocumentBuilder(mode_registry=registry).build(session)

        readiness = ReportReadinessService(mode_registry=registry).assess_request(
            document,
            ReportRequest(document.session.id, "process_review"),
        )

        self.assertNotEqual(ReadinessStatus.VALIDATION_FAILED, readiness.status)
        self.assertNotIn(
            "missing_process_context",
            {finding.code for finding in readiness.all_findings()},
        )
