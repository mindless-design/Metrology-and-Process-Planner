import tempfile
import unittest
from dataclasses import replace
from pathlib import Path

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
from metrology_process_planner.persistence.paths import SessionPaths, artifact_path_to_disk
from metrology_process_planner.reporting import ReportGenerationService, ReportRequest
from metrology_process_planner.workflows.artifacts import ArtifactRepairService, ArtifactScanner
from metrology_process_planner.workflows.artifacts.requests import (
    RepairRequestStatus,
    RepairType,
)
from metrology_process_planner.workflows.editor import (
    DefaultSessionModeAdapter,
    EditorActionType,
    SessionDocumentBuilder,
)
from tests.reporting_workbench_fixtures import document_with_artifact


def _generated_report_session(paths: SessionPaths, output_formats=("pptx",)):
    document = document_with_artifact(ArtifactStatus.PRESENT)
    result = ReportGenerationService().generate(
        document,
        ReportRequest(document.session.id, "metrology_report", output_formats=output_formats),
        paths.folder,
    )
    assert result.updated_session is not None
    return result.updated_session

def _pptx_artifact(session):
    return _artifact_by_type(session, "powerpoint_deck")

def _artifact_by_type(session, artifact_type):
    return next(
        artifact
        for artifact in (session.artifacts or {}).values()
        if artifact.type == artifact_type
    )

def _process_artifact() -> ArtifactRecord:
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

def _process_warning() -> WarningRecord:
    return WarningRecord(
        "legacy-process-warning",
        "Legacy process output is stale.",
        source="process_output",
        code="PROCESS_OUTPUT_STALE",
        related_artifact_refs=("legacy-process-output",),
    )

def _recipe_free_profilometry_registry() -> ModeRegistry:
    return ModeRegistry(
        (ModeDefinition(SessionMode.PROFILOMETRY_PLANNER.value, "Recipe Free Override"),)
    )

if __name__ == "__main__":
    unittest.main()


class ReportArtifactRepairTestsPart1(unittest.TestCase):
    def test_generated_report_artifacts_have_available_repair_request(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            paths = SessionPaths.for_folder(Path(temp_dir))
            report_session = _generated_report_session(paths)
            artifact = _pptx_artifact(report_session)
            source = replace(
                report_session,
                artifacts={
                    **dict(report_session.artifacts),
                    artifact.id: replace(artifact, status=ArtifactStatus.STALE),
                },
            )

            request = next(
                item
                for item in ArtifactRepairService().build_repair_requests(source)
                if item.artifact_id == artifact.id
            )

        self.assertEqual(RepairType.REBUILD_REPORT, request.repair_type)
        self.assertEqual(RepairRequestStatus.AVAILABLE, request.status)

    def test_report_artifact_signature_uses_loaded_recipe_free_registry(self) -> None:
        registry = _recipe_free_profilometry_registry()
        with tempfile.TemporaryDirectory() as temp_dir:
            paths = SessionPaths.for_folder(Path(temp_dir))
            document = document_with_artifact(ArtifactStatus.PRESENT)
            document = SessionDocumentBuilder(mode_registry=registry).build(
                replace(document.session, mode=SessionMode.PROFILOMETRY_PLANNER)
            )
            result = ReportGenerationService(mode_registry=registry).generate(
                document,
                ReportRequest(document.session.id, "engineering_review"),
                paths.folder,
            )
            assert result.updated_session is not None
            artifact = _pptx_artifact(result.updated_session)
            changed = replace(
                result.updated_session,
                artifacts={
                    **dict(result.updated_session.artifacts or {}),
                    "legacy-process-output": _process_artifact(),
                },
                warnings=(_process_warning(),),
            )

            scanned, _scan_result = ArtifactScanner().scan_session(changed, paths, registry)

        self.assertEqual(ArtifactStatus.PRESENT, scanned.artifacts[artifact.id].status)
        self.assertEqual((), scanned.artifacts[artifact.id].warning_ids)

    def test_powerpoint_report_repair_rebuilds_missing_deck(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            paths = SessionPaths.for_folder(Path(temp_dir))
            report_session = _generated_report_session(paths)
            artifact = _pptx_artifact(report_session)
            artifact_path_to_disk(paths.folder, artifact.relative_path).unlink()
            missing = replace(artifact, status=ArtifactStatus.MISSING)
            source = replace(
                report_session,
                artifacts={**dict(report_session.artifacts), artifact.id: missing},
            )

            repaired = ArtifactRepairService().repair_artifact(source, artifact.id, paths)
            repaired_artifact = repaired.artifacts[artifact.id]
            output_exists = artifact_path_to_disk(
                paths.folder,
                repaired_artifact.relative_path,
            ).exists()

        self.assertEqual(ArtifactStatus.PRESENT, repaired_artifact.status)
        self.assertTrue(output_exists)
        self.assertEqual(artifact.id, repaired.reports[0].artifact_refs["powerpoint_deck"])

    def test_report_item_exposes_artifact_repair_actions_in_editor(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            paths = SessionPaths.for_folder(Path(temp_dir))
            report_session = _generated_report_session(paths)
            artifact = _pptx_artifact(report_session)
            source = replace(
                report_session,
                artifacts={
                    **dict(report_session.artifacts),
                    artifact.id: replace(artifact, status=ArtifactStatus.STALE),
                },
            )

            document = SessionDocumentBuilder().build(source)
            item = document.items_by_id[f"report:{source.reports[0].id}"]
            adapter = DefaultSessionModeAdapter()
            actions = adapter.actions(source, item)
            fields = adapter.metadata_fields(source, item)
            previews = adapter.preview_options(source, item)

        repair_actions = [
            action
            for action in actions
            if action.action_type is EditorActionType.REGENERATE_ARTIFACT
        ]
        relink_actions = [
            action
            for action in actions
            if action.action_type is EditorActionType.RELINK_ARTIFACT
        ]
        repair_payloads = [dict(action.payload) for action in repair_actions]
        field_values = {field.key: field.value for field in fields}

        self.assertIn({"artifact_id": artifact.id}, repair_payloads)
        self.assertTrue(relink_actions)
        self.assertIn(artifact.id, tuple(ref.artifact_id for ref in item.artifact_refs))
        self.assertEqual(source.reports[0].label, field_values["label"])
        self.assertEqual(source.reports[0].report_type, field_values["report_type"])
        self.assertEqual("ready", field_values["status"])
        self.assertEqual(str(len(source.reports[0].artifact_refs)), field_values["artifact_count"])
        self.assertIn("PowerPoint Deck", tuple(preview.label for preview in previews))
        self.assertIn("Report Manifest", tuple(preview.label for preview in previews))
        self.assertTrue(any(preview.status == "stale" for preview in previews))
