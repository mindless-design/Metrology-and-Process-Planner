from metrology_process_planner.domains.session import (
    ArtifactOwnerRef,
    ArtifactRecord,
    ArtifactRepairMetadata,
    ArtifactStatus,
    ModeDefinition,
    ModeRegistry,
    SessionMode,
    WarningRecord,
)
from metrology_process_planner.persistence.paths import SessionPaths
from metrology_process_planner.reporting import ReportGenerationService, ReportRequest
from tests.reporting_workbench_fixtures import document_with_artifact


def generated_report_session(paths: SessionPaths, output_formats=("pptx",)):
    document = document_with_artifact(ArtifactStatus.PRESENT)
    result = ReportGenerationService().generate(
        document,
        ReportRequest(document.session.id, "metrology_report", output_formats=output_formats),
        paths.folder,
    )
    assert result.updated_session is not None
    return result.updated_session


def pptx_artifact(session):
    return artifact_by_type(session, "powerpoint_deck")


def artifact_by_type(session, artifact_type):
    return next(
        artifact
        for artifact in (session.artifacts or {}).values()
        if artifact.type == artifact_type
    )


def process_artifact() -> ArtifactRecord:
    return ArtifactRecord(
        "legacy-process-output",
        "process_output",
        "Legacy Process Output",
        "process_outputs/legacy-stack.png",
        ArtifactOwnerRef("capture", "cap-001", "stack_image"),
        status=ArtifactStatus.MISSING,
        repair=ArtifactRepairMetadata(
            repair_action="regenerate_process_output",
            regenerable=True,
            requires_recipe=True,
            requires_solver=True,
        ),
    )


def process_warning() -> WarningRecord:
    return WarningRecord(
        "legacy-process-warning",
        "Legacy process output is stale.",
        source="process_output",
        code="PROCESS_OUTPUT_STALE",
        related_artifact_refs=("legacy-process-output",),
    )


def recipe_free_profilometry_registry() -> ModeRegistry:
    return ModeRegistry(
        (ModeDefinition(SessionMode.PROFILOMETRY_PLANNER.value, "Recipe Free Override"),)
    )
