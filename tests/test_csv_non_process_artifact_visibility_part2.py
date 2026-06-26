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
)
from metrology_process_planner.persistence.csv_export import CaptureCsvExporter
from tests.artifact_helpers import capture_crop_artifact
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


class CsvNonProcessArtifactVisibilityTestsPart2(unittest.TestCase):
    def test_recipe_free_csv_hides_capture_owned_process_artifacts(self) -> None:
        source = saved_capture_session()
        visible = capture_crop_artifact()
        hidden = ArtifactRecord(
            "legacy-capture-process-output",
            "process_output",
            "Legacy Capture Stack",
            "process_outputs/cap-001-stack.png",
            ArtifactOwnerRef("capture", "cap-001", "stack_image"),
            status=ArtifactStatus.MISSING,
            repair=ArtifactRepairMetadata(
                repair_action="regenerate_process_output",
                requires_recipe=True,
                requires_solver=True,
            ),
        )
        session = replace(source, artifacts={visible.id: visible, hidden.id: hidden})

        row = CaptureCsvExporter().rows_for_session(session)[0]

        self.assertEqual(visible.id, row["site_image_artifact_id"])
        self.assertIn("crop:present", row["artifact_statuses"])
        self.assertNotIn("stack_image:missing", row["artifact_statuses"])
        self.assertNotIn("process_outputs/cap-001-stack.png", row["image_paths"])

    def test_loaded_recipe_free_registry_hides_process_artifacts_for_process_named_mode(
        self,
    ) -> None:
        source = replace(saved_capture_session(), mode=SessionMode.PROFILOMETRY_PLANNER)
        visible = capture_crop_artifact()
        hidden = ArtifactRecord(
            "legacy-capture-process-output",
            "process_output",
            "Legacy Capture Stack",
            "process_outputs/cap-001-stack.png",
            ArtifactOwnerRef("capture", "cap-001", "stack_image"),
            status=ArtifactStatus.MISSING,
            repair=ArtifactRepairMetadata(
                repair_action="regenerate_process_output",
                requires_recipe=True,
                requires_solver=True,
            ),
        )
        session = replace(source, artifacts={visible.id: visible, hidden.id: hidden})

        exporter = CaptureCsvExporter(
            mode_registry=_recipe_free_registry_for(source.mode.value)
        )
        row = exporter.rows_for_session(session)[0]

        self.assertIn("crop:present", row["artifact_statuses"])
        self.assertNotIn("stack_image:missing", row["artifact_statuses"])
        self.assertNotIn("process_outputs/cap-001-stack.png", row["image_paths"])

    def test_recipe_free_csv_hides_generic_images_with_process_roles(self) -> None:
        source = saved_capture_session()
        visible = capture_crop_artifact()
        hidden = ArtifactRecord(
            "legacy-stack-image",
            "image",
            "Legacy Stack Image",
            "images/cap-001-stack.png",
            ArtifactOwnerRef("capture", "cap-001", "stack_image"),
            status=ArtifactStatus.PRESENT,
        )
        session = replace(source, artifacts={visible.id: visible, hidden.id: hidden})

        row = CaptureCsvExporter().rows_for_session(session)[0]

        self.assertIn("crop:present", row["artifact_statuses"])
        self.assertNotIn("stack_image:present", row["artifact_statuses"])
        self.assertNotIn("images/cap-001-stack.png", row["image_paths"])

    def test_recipe_free_csv_hides_external_process_artifact_name_variants(self) -> None:
        source = saved_capture_session()
        visible = capture_crop_artifact()
        hidden = ArtifactRecord(
            "legacy-stack-image-png",
            "Stack Image PNG",
            "Legacy Stack Image",
            "images/cap-001-stack.png",
            ArtifactOwnerRef("capture", "cap-001", "Stack Image PNG"),
            status=ArtifactStatus.PRESENT,
        )
        session = replace(source, artifacts={visible.id: visible, hidden.id: hidden})

        row = CaptureCsvExporter().rows_for_session(session)[0]

        self.assertIn("crop:present", row["artifact_statuses"])
        self.assertNotIn("Stack Image PNG:present", row["artifact_statuses"])
        self.assertNotIn("images/cap-001-stack.png", row["image_paths"])
