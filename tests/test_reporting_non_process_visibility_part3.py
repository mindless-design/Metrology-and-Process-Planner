import unittest
from dataclasses import replace

from metrology_process_planner.domains.session import (
    ArtifactOwnerRef,
    ArtifactRecord,
    ArtifactRepairMetadata,
    ArtifactStatus,
    ModeDefinition,
    ModeRegistry,
    ReportRecord,
    SessionMode,
    WarningRecord,
)
from metrology_process_planner.workflows.editor.adapters import DefaultSessionModeAdapter
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


class ReportingNonProcessVisibilityTestsPart3(unittest.TestCase):
    def test_loaded_recipe_free_report_inspector_counts_only_visible_records(
        self,
    ) -> None:
        registry = _recipe_free_registry_for(SessionMode.PROFILOMETRY_PLANNER.value)
        source = _report_with_hidden_process_artifact()
        document = SessionDocumentBuilder(mode_registry=registry).build(source)
        item = document.items_by_id["report:report-001"]

        fields = {
            field.key: field.value
            for field in DefaultSessionModeAdapter(registry).metadata_fields(source, item)
        }

        self.assertEqual("1", fields["artifact_count"])
        self.assertEqual("1", fields["warning_count"])


def _report_with_hidden_process_artifact():
    visible_artifact = _visible_report_artifact()
    hidden_artifact = _hidden_process_report_artifact()
    return replace(
        session_without_pending(),
        mode=SessionMode.PROFILOMETRY_PLANNER,
        reports=(_report_record(visible_artifact.id, hidden_artifact.id),),
        artifacts={
            visible_artifact.id: visible_artifact,
            hidden_artifact.id: hidden_artifact,
        },
        warnings=_report_warnings(visible_artifact.id, hidden_artifact.id),
    )


def _visible_report_artifact() -> ArtifactRecord:
    return ArtifactRecord(
        "visible-report",
        "report_pdf",
        "Report PDF",
        "reports/summary.pdf",
        ArtifactOwnerRef("report", "report-001", "pdf"),
        status=ArtifactStatus.PRESENT,
    )


def _hidden_process_report_artifact() -> ArtifactRecord:
    return ArtifactRecord(
        "legacy-process-output",
        "process_output",
        "Legacy Stack Image",
        "process_outputs/legacy-stack.png",
        ArtifactOwnerRef("report", "report-001", "stack_image"),
        status=ArtifactStatus.MISSING,
        repair=_process_repair(),
    )


def _report_record(visible_id: str, hidden_id: str) -> ReportRecord:
    return ReportRecord(
        "report-001",
        "Summary",
        "capture_catalog",
        artifact_refs={"pdf": visible_id, "stack_image": hidden_id},
        warning_ids=("visible-warning", "hidden-process-warning"),
    )


def _report_warnings(visible_id: str, hidden_id: str) -> tuple[WarningRecord, ...]:
    return (
        WarningRecord(
            "visible-warning",
            "Report PDF is stale.",
            source="artifact",
            code="ARTIFACT_STALE",
            related_artifact_refs=(visible_id,),
        ),
        WarningRecord(
            "hidden-process-warning",
            "Recipe missing.",
            source="process_context",
            code="PROCESS_RECIPE_MISSING",
            related_artifact_refs=(hidden_id,),
        ),
    )
