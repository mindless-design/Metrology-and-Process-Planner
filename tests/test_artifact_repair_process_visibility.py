import unittest
from dataclasses import replace

from metrology_process_planner.domains.session import (
    ArtifactRepairMetadata,
    ArtifactStatus,
    ModeDefinition,
    ModeRegistry,
    SessionMode,
    SessionModeId,
    WarningRecord,
)
from metrology_process_planner.workflows.artifacts import ArtifactRepairService
from tests.artifact_lifecycle_fixtures import artifact as make_artifact
from tests.artifact_lifecycle_fixtures import session, temp_paths


class ArtifactRepairProcessVisibilityTests(unittest.TestCase):
    def test_process_only_repair_artifact_is_hidden_for_recipe_free_session(self) -> None:
        target = _process_artifact(ArtifactStatus.MISSING)
        source = session(artifacts={"process-output": target})
        service = ArtifactRepairService()

        requests = service.build_repair_requests(source)
        repaired = service.repair_artifact(source, "process-output", temp_paths())

        self.assertEqual((), requests)
        self.assertEqual(ArtifactStatus.MISSING, repaired.artifacts["process-output"].status)
        self.assertEqual((), repaired.warnings)

    def test_scan_preserves_hidden_process_only_artifact_for_recipe_free_session(self) -> None:
        target = _process_artifact(ArtifactStatus.PRESENT)
        source = session(artifacts={"process-output": target})

        scanned, result = ArtifactRepairService().scan_session(source, temp_paths())

        self.assertEqual(ArtifactStatus.PRESENT, scanned.artifacts["process-output"].status)
        self.assertEqual(0, result.artifact_count)
        self.assertEqual(0, result.missing_count)
        self.assertEqual((), result.warning_ids)
        self.assertEqual((), scanned.warnings)

    def test_scan_uses_loaded_recipe_free_registry_for_process_named_artifacts(self) -> None:
        registry = ModeRegistry((ModeDefinition("external_mode", "External Mode"),))
        target = _process_artifact(ArtifactStatus.PRESENT)
        source = replace(
            session(artifacts={"process-output": target}),
            mode=SessionModeId("external_mode"),
        )

        scanned, result = ArtifactRepairService().scan_session(
            source,
            temp_paths(),
            registry,
        )

        self.assertEqual(ArtifactStatus.PRESENT, scanned.artifacts["process-output"].status)
        self.assertEqual(0, result.artifact_count)
        self.assertEqual(0, result.missing_count)
        self.assertEqual((), result.warning_ids)
        self.assertEqual((), scanned.warnings)

    def test_scan_summary_uses_loaded_recipe_free_registry_for_builtin_override(
        self,
    ) -> None:
        registry = _recipe_free_profilometry_registry()
        target = _process_artifact(ArtifactStatus.MISSING)
        warning = _process_warning("process-output")
        source = replace(
            session(artifacts={"process-output": target}),
            mode=SessionMode.PROFILOMETRY_PLANNER,
            warnings=(warning,),
        )

        scanned, result = ArtifactRepairService().scan_session(
            source,
            temp_paths(),
            registry,
        )

        self.assertEqual(ArtifactStatus.MISSING, scanned.artifacts["process-output"].status)
        self.assertEqual(0, result.artifact_count)
        self.assertEqual(0, result.missing_count)
        self.assertEqual((), result.warning_ids)
        self.assertEqual((warning,), scanned.warnings)


def _process_artifact(status: ArtifactStatus):
    return replace(
        make_artifact("process-output"),
        type="process_output",
        status=status,
        repair=ArtifactRepairMetadata(
            repair_action="regenerate_process_output",
            regenerable=True,
            requires_recipe=True,
            requires_solver=True,
        ),
    )

def _process_warning(artifact_id: str) -> WarningRecord:
    return WarningRecord(
        f"{artifact_id}:process-stale",
        "Process output is stale.",
        source="process_output",
        code="PROCESS_OUTPUT_STALE",
        related_artifact_refs=(artifact_id,),
    )

def _recipe_free_profilometry_registry() -> ModeRegistry:
    return ModeRegistry(
        (ModeDefinition(SessionMode.PROFILOMETRY_PLANNER.value, "Recipe Free Override"),)
    )
