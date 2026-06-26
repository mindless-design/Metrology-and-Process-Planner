import csv
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
    SessionMode,
    WarningRecord,
)
from metrology_process_planner.persistence.csv_export import CaptureCsvExporter
from metrology_process_planner.workflows.grid_measurement import create_grid_dataset
from tests.test_grid_measurement_workflow import _session

if __name__ == "__main__":
    unittest.main()


class GridMeasurementCsvExportTests(unittest.TestCase):
    def test_csv_export_includes_generated_grid_site_rows(self) -> None:
        session = create_grid_dataset(_session(), "cap-a", "cap-b", 2, 3, "Gate grid")

        with TemporaryDirectory() as temp_dir:
            path = CaptureCsvExporter().export(session, Path(temp_dir) / "captures.csv")
            with path.open(encoding="utf-8") as handle:
                rows = list(csv.DictReader(handle))

        grid_rows = [row for row in rows if row["row_kind"] == "grid_site"]

        self.assertEqual(2, len([row for row in rows if row["row_kind"] == "capture"]))
        self.assertEqual(6, len(grid_rows))
        self.assertEqual("grid-001:site-001", grid_rows[0]["capture_id"])
        self.assertEqual("Gate grid R01C01", grid_rows[0]["label"])
        self.assertEqual("grid-001:site-006", grid_rows[-1]["capture_id"])
        self.assertEqual("Gate grid R02C03", grid_rows[-1]["label"])
        self.assertEqual("Gate grid", grid_rows[0]["grid_dataset_label"])
        self.assertEqual("1", grid_rows[0]["grid_row"])
        self.assertEqual("1", grid_rows[0]["grid_column"])
        self.assertEqual("5.0", grid_rows[0]["grid_center_x"])
        self.assertEqual("5.0", grid_rows[0]["grid_center_y"])
        self.assertEqual("cap-a;cap-b", grid_rows[0]["grid_anchor_capture_ids"])
        self.assertEqual("placeholder", grid_rows[0]["grid_overview_artifact_status"])
        self.assertEqual("1", grid_rows[0]["warning_count"])

    def test_loaded_recipe_free_registry_hides_process_grid_overview_artifact(
        self,
    ) -> None:
        registry = ModeRegistry(
            (ModeDefinition(SessionMode.PROFILOMETRY_PLANNER.value, "Recipe Free Override"),)
        )
        session = _grid_session_with_hidden_process_overview()

        row = next(
            row
            for row in CaptureCsvExporter(mode_registry=registry).rows_for_session(session)
            if row["row_kind"] == "grid_site"
        )

        self.assertEqual("", row["grid_overview_artifact_id"])
        self.assertEqual("", row["grid_overview_artifact_status"])
        self.assertEqual("", row["artifact_statuses"])
        self.assertEqual("0", row["warning_count"])


def _grid_session_with_hidden_process_overview():
    source = create_grid_dataset(_session(), "cap-a", "cap-b", 1, 1, "Gate grid")
    hidden_process = _hidden_process_grid_overview()
    dataset = replace(
        source.grid_datasets[0],
        artifact_refs={"grid_overview": hidden_process.id},
        warning_ids=("hidden-process-warning",),
    )
    return replace(
        source,
        mode=SessionMode.PROFILOMETRY_PLANNER,
        grid_datasets=(dataset,),
        artifacts={hidden_process.id: hidden_process},
        warnings=_hidden_grid_warnings(hidden_process.id),
    )


def _hidden_process_grid_overview() -> ArtifactRecord:
    return ArtifactRecord(
        "legacy-process-grid-overview",
        "process_output",
        "Legacy Grid Stack",
        "process_outputs/grid-stack.png",
        ArtifactOwnerRef("grid_dataset", "grid-001", "stack_image"),
        status=ArtifactStatus.MISSING,
        repair=ArtifactRepairMetadata(
            repair_action="regenerate_process_output",
            requires_recipe=True,
            requires_solver=True,
        ),
    )


def _hidden_grid_warnings(artifact_id: str) -> tuple[WarningRecord, ...]:
    return (
        WarningRecord(
            "hidden-process-warning",
            "Recipe-backed grid overview is unavailable.",
            source="process_output",
            code="PROCESS_OUTPUT_STALE",
            related_artifact_refs=(artifact_id,),
        ),
    )
