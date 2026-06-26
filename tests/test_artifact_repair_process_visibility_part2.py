import unittest
from dataclasses import replace

from metrology_process_planner.domains.session import (
    ArtifactDependencyRef,
    ArtifactRepairMetadata,
    ArtifactStatus,
    ModeDefinition,
    ModeRegistry,
    SessionMode,
    WarningRecord,
)
from metrology_process_planner.workflows.artifacts import ArtifactRepairService
from metrology_process_planner.workflows.artifacts.signatures import current_signature
from tests.artifact_lifecycle_fixtures import artifact as make_artifact
from tests.artifact_lifecycle_fixtures import scan_with_file, session, temp_paths


class ArtifactRepairProcessVisibilityTestsPart2(unittest.TestCase):
    def test_session_data_freshness_uses_loaded_recipe_free_registry_for_builtin_override(
        self,
    ) -> None:
        registry = _recipe_free_profilometry_registry()
        visible = make_artifact("visible", path="images/visible.png")
        base = replace(
            session(artifacts={"visible": visible}),
            mode=SessionMode.PROFILOMETRY_PLANNER,
        )
        signature = current_signature(base, "session_data", base.id, registry)
        visible = replace(
            visible,
            dependencies=(
                ArtifactDependencyRef(
                    kind="session_data",
                    id=base.id,
                    signature=signature,
                ),
            ),
        )
        hidden = _process_artifact(ArtifactStatus.MISSING)
        changed = replace(
            base,
            artifacts={"visible": visible, "process-output": hidden},
            warnings=(_process_warning("process-output"),),
        )

        scanned, _result = scan_with_file(changed, "images/visible.png", registry)

        self.assertEqual(ArtifactStatus.PRESENT, scanned.artifacts["visible"].status)
        self.assertEqual((), scanned.artifacts["visible"].warning_ids)
        self.assertEqual(ArtifactStatus.MISSING, scanned.artifacts["process-output"].status)

    def test_bulk_repair_uses_loaded_recipe_free_registry_for_process_named_artifacts(
        self,
    ) -> None:
        registry = ModeRegistry(
            (ModeDefinition(SessionMode.PROFILOMETRY_PLANNER.value, "Recipe Free Override"),)
        )
        target = _process_artifact(ArtifactStatus.MISSING)
        source = replace(
            session(artifacts={"process-output": target}),
            mode=SessionMode.PROFILOMETRY_PLANNER,
        )

        repaired = ArtifactRepairService().repair_all_missing(
            source,
            temp_paths(),
            registry,
        )

        self.assertEqual(ArtifactStatus.MISSING, repaired.artifacts["process-output"].status)
        self.assertEqual((), repaired.artifacts["process-output"].warning_ids)
        self.assertEqual((), repaired.warnings)

    def test_relink_uses_loaded_recipe_free_registry_for_process_named_artifacts(
        self,
    ) -> None:
        registry = ModeRegistry(
            (ModeDefinition(SessionMode.PROFILOMETRY_PLANNER.value, "Recipe Free Override"),)
        )
        target = _process_artifact(ArtifactStatus.MISSING)
        source = replace(
            session(artifacts={"process-output": target}),
            mode=SessionMode.PROFILOMETRY_PLANNER,
        )

        relinked = ArtifactRepairService().relink_artifact(
            source,
            "process-output",
            "images/relinked.png",
            registry,
        )

        self.assertEqual(
            target.relative_path,
            relinked.artifacts["process-output"].relative_path,
        )
        self.assertEqual((), relinked.warnings)


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
