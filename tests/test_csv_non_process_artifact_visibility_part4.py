import unittest
from dataclasses import replace

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
from metrology_process_planner.persistence.csv_export import CaptureCsvExporter
from tests.measurement_child_fixtures import saved_capture_session


def _process_artifact(artifact_id: str) -> ArtifactRecord:
    return ArtifactRecord(
        artifact_id,
        "process_output",
        "Legacy Process Output",
        "process_outputs/legacy.json",
        ArtifactOwnerRef("measurement", "meas-001", "measurement_detail"),
        status=ArtifactStatus.MISSING,
        repair=ArtifactRepairMetadata(
            repair_action="regenerate_process_output",
            requires_recipe=True,
            requires_solver=True,
        ),
    )

def _recipe_free_registry_for(mode_id: str) -> ModeRegistry:
    return ModeRegistry((ModeDefinition(mode_id, "Recipe Free Override"),))

if __name__ == "__main__":
    unittest.main()


class CsvNonProcessArtifactVisibilityTestsPart4(unittest.TestCase):
    def test_recipe_free_csv_still_ignores_hidden_owned_process_artifact_warning(self) -> None:
        source = saved_capture_session()
        hidden = replace(
            _process_artifact("legacy-owned-stack-image"),
            owner=ArtifactOwnerRef("capture", "cap-001", "stack_image"),
            warning_ids=("hidden-owned-process-warning",),
        )
        session = replace(
            source,
            artifacts={**dict(source.artifacts or {}), hidden.id: hidden},
            warnings=(
                WarningRecord(
                    "hidden-owned-process-warning",
                    "Legacy stack image is missing.",
                    source="artifacts",
                    code="ARTIFACT_MISSING",
                    related_artifact_refs=(hidden.id,),
                ),
            ),
        )

        row = CaptureCsvExporter().rows_for_session(session)[0]

        self.assertNotIn("stack_image:missing", row["artifact_statuses"])
        self.assertEqual(0, row["warning_count"])

    def test_recipe_free_csv_warning_count_ignores_process_only_capture_warnings(self) -> None:
        source = saved_capture_session()
        session = replace(
            source,
            warnings=(
                WarningRecord(
                    "solver-warning",
                    "Solver backend unavailable.",
                    source="solver",
                    code="SOLVER_BACKEND_UNAVAILABLE",
                    related_item_refs=("capture:cap-001",),
                ),
                WarningRecord(
                    "render-warning",
                    "Render profile missing.",
                    source="render_profile",
                    code="RENDER_PROFILE_MISSING",
                    related_item_refs=("capture:cap-001",),
                ),
                WarningRecord(
                    "artifact-warning",
                    "Capture artifact missing.",
                    source="artifact",
                    code="ARTIFACT_MISSING",
                    related_item_refs=("capture:cap-001",),
                ),
            ),
        )

        row = CaptureCsvExporter().rows_for_session(session)[0]

        self.assertEqual(1, row["warning_count"])

    def test_loaded_recipe_free_registry_ignores_process_warning_for_process_named_mode(
        self,
    ) -> None:
        source = replace(saved_capture_session(), mode=SessionMode.PROFILOMETRY_PLANNER)
        session = replace(
            source,
            warnings=(
                WarningRecord(
                    "solver-warning",
                    "Solver backend unavailable.",
                    source="solver",
                    code="SOLVER_BACKEND_UNAVAILABLE",
                    related_item_refs=("capture:cap-001",),
                ),
            ),
        )

        exporter = CaptureCsvExporter(
            mode_registry=_recipe_free_registry_for(source.mode.value)
        )
        row = exporter.rows_for_session(session)[0]

        self.assertEqual(0, row["warning_count"])

    def test_recipe_free_csv_preserves_legacy_string_tags(self) -> None:
        source = saved_capture_session()
        capture = replace(source.captures[0], metadata={"tags": "overlay;alignment"})
        session = replace(source, captures=(capture,))

        row = CaptureCsvExporter().rows_for_session(session)[0]

        self.assertEqual("overlay;alignment", row["tags"])
