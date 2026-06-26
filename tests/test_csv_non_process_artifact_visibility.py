import unittest
from dataclasses import replace
from pathlib import Path
from tempfile import TemporaryDirectory

from metrology_process_planner.domains.geometry import Point
from metrology_process_planner.domains.measurement.records import MeasurementRecord
from metrology_process_planner.domains.session import (
    ArtifactOwnerRef,
    ArtifactRecord,
    ArtifactRepairMetadata,
    ArtifactStatus,
    ModeDefinition,
    ModeRegistry,
)
from metrology_process_planner.persistence.csv_export import CaptureCsvExporter
from metrology_process_planner.persistence.paths import SessionPaths
from tests.measurement_child_fixtures import saved_measurement_document


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


class CsvNonProcessArtifactVisibilityTestsPart1(unittest.TestCase):
    def test_recipe_free_csv_row_includes_geometry_measurements_and_artifacts(self) -> None:
        with TemporaryDirectory() as temp_dir:
            document = saved_measurement_document(SessionPaths.for_folder(Path(temp_dir)))

        row = CaptureCsvExporter().rows_for_session(document.session)[0]

        self.assertEqual("session-001", row["session_id"])
        self.assertEqual("simple_capture", row["mode_id"])
        self.assertEqual("cap-001", row["capture_id"])
        self.assertEqual("Site", row["label"])
        self.assertEqual(0.0, row["left"])
        self.assertEqual(5.0, row["right"])
        self.assertEqual(0.0, row["bottom"])
        self.assertEqual(5.0, row["top"])
        self.assertEqual(2.5, row["center_x"])
        self.assertEqual(2.5, row["center_y"])
        self.assertEqual(5.0, row["width"])
        self.assertEqual(5.0, row["height"])
        self.assertEqual("meas-001", row["measurement_id"])
        self.assertEqual("Gate CD", row["measurement_label"])
        self.assertEqual("cd", row["measurement_type"])
        self.assertEqual(3.0, row["measurement_length"])
        self.assertEqual("3.0", row["target"])
        self.assertEqual("2.5", row["lsl"])
        self.assertEqual("3.5", row["usl"])
        self.assertEqual("outer_edges", row["edge_convention"])
        self.assertEqual("meas-001", row["measurement_ids"])
        self.assertEqual("Gate CD", row["measurement_labels"])
        self.assertEqual("cd", row["measurement_types"])
        self.assertEqual("3.0", row["measurement_lengths"])
        self.assertEqual("3.0", row["measurement_targets"])
        self.assertEqual("2.5", row["measurement_lsl"])
        self.assertEqual("3.5", row["measurement_usl"])
        self.assertEqual("outer_edges", row["measurement_edge_conventions"])
        self.assertEqual("present", row["measurement_artifact_status"])
        self.assertIn("layout_annotation_svg:present", row["artifact_statuses"])
        self.assertEqual(0, row["warning_count"])

    def test_recipe_free_csv_summarizes_all_nested_measurement_artifacts(self) -> None:
        with TemporaryDirectory() as temp_dir:
            document = saved_measurement_document(SessionPaths.for_folder(Path(temp_dir)))
        source = document.session
        first = source.captures[0].measurements[0]
        second_artifact = ArtifactRecord(
            "measurement-meas-002-detail",
            "measurement_detail",
            "Second Measurement Detail",
            "drawings/measurements/meas-002.svg",
            ArtifactOwnerRef("measurement", "meas-002", "measurement_detail"),
            status=ArtifactStatus.MISSING,
        )
        second = MeasurementRecord(
            "meas-002",
            "Space CD",
            Point(1, 2),
            Point(4, 2),
            edge_detection_convention="inner_edges",
            artifact_refs={"measurement_detail": second_artifact.id},
            metadata={"measurement_type": "space"},
        )
        capture = replace(source.captures[0], measurements=(first, second))
        session = replace(
            source,
            captures=(capture,),
            artifacts={**dict(source.artifacts or {}), second_artifact.id: second_artifact},
        )

        row = CaptureCsvExporter().rows_for_session(session)[0]

        self.assertEqual("meas-001;meas-002", row["measurement_ids"])
        self.assertEqual("cd;space", row["measurement_types"])
        self.assertEqual("outer_edges;inner_edges", row["measurement_edge_conventions"])
        self.assertEqual(
            first.artifact_refs["measurement_annotation_svg"],
            row["measurement_artifact_id"],
        )
        self.assertIn("measurement_annotation_svg:present", row["artifact_statuses"])
        self.assertIn("measurement_detail:missing", row["artifact_statuses"])
        self.assertIn("drawings/measurements/meas-002.svg", row["image_paths"])
