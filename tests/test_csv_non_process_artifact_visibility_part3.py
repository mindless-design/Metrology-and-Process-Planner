import unittest
from dataclasses import replace
from pathlib import Path
from tempfile import TemporaryDirectory

from metrology_process_planner.domains.session import (
    ArtifactOwnerRef,
    ArtifactRecord,
    ArtifactRepairMetadata,
    ArtifactStatus,
    ModeDefinition,
    ModeRegistry,
    WarningRecord,
)
from metrology_process_planner.persistence.csv_export import CaptureCsvExporter
from metrology_process_planner.persistence.paths import SessionPaths
from tests.measurement_child_fixtures import saved_capture_session, saved_measurement_document


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


class CsvNonProcessArtifactVisibilityTestsPart3(unittest.TestCase):
    def test_recipe_free_csv_measurement_artifact_falls_back_after_hidden_process_ref(self) -> None:
        with TemporaryDirectory() as temp_dir:
            document = saved_measurement_document(SessionPaths.for_folder(Path(temp_dir)))
        source = document.session
        visible_id = source.captures[0].measurements[0].artifact_refs["annotation"]
        hidden = _process_artifact("legacy-measurement-process-output")
        measurement = replace(
            source.captures[0].measurements[0],
            artifact_refs={
                **dict(source.captures[0].measurements[0].artifact_refs),
                "measurement_detail": hidden.id,
            },
        )
        capture = replace(source.captures[0], measurements=(measurement,))
        session = replace(
            source,
            captures=(capture,),
            artifacts={**dict(source.artifacts or {}), hidden.id: hidden},
        )

        row = CaptureCsvExporter().rows_for_session(session)[0]

        self.assertEqual(visible_id, row["measurement_artifact_id"])
        self.assertNotEqual(hidden.id, row["measurement_artifact_id"])

    def test_recipe_free_csv_warning_count_ignores_hidden_process_artifact_warnings(self) -> None:
        source = saved_capture_session()
        hidden = replace(
            _process_artifact("legacy-capture-process-output"),
            owner=ArtifactOwnerRef("capture", "cap-001", "stack_image"),
            warning_ids=("hidden-artifact-warning",),
        )
        capture = replace(
            source.captures[0],
            artifact_refs={
                **dict(source.captures[0].artifact_refs or {}),
                "stack_image": hidden.id,
            },
        )
        session = replace(
            source,
            captures=(capture,),
            artifacts={**dict(source.artifacts or {}), hidden.id: hidden},
            warnings=(
                WarningRecord(
                    "hidden-artifact-warning",
                    "Hidden process artifact is missing.",
                    source="artifacts",
                    code="ARTIFACT_MISSING",
                ),
            ),
        )

        row = CaptureCsvExporter().rows_for_session(session)[0]

        self.assertEqual(0, row["warning_count"])

    def test_recipe_free_csv_counts_visible_owned_artifact_warning_without_local_ref(self) -> None:
        source = saved_capture_session()
        visible = ArtifactRecord(
            "capture-review-annotation",
            "svg",
            "Review Annotation",
            "drawings/captures/cap-001-review.svg",
            ArtifactOwnerRef("capture", "cap-001", "review_annotation_svg"),
            status=ArtifactStatus.MISSING,
            warning_ids=("review-annotation-missing",),
        )
        session = replace(
            source,
            artifacts={**dict(source.artifacts or {}), visible.id: visible},
            warnings=(
                WarningRecord(
                    "review-annotation-missing",
                    "Review annotation is missing.",
                    source="artifacts",
                    code="ARTIFACT_MISSING",
                    related_artifact_refs=(visible.id,),
                ),
            ),
        )

        row = CaptureCsvExporter().rows_for_session(session)[0]

        self.assertIn("review_annotation_svg:missing", row["artifact_statuses"])
        self.assertEqual(1, row["warning_count"])
