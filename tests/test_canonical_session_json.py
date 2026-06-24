import json
import tempfile
import unittest
from pathlib import Path

from metrology_process_planner.domains.geometry import Box, Point
from metrology_process_planner.domains.measurements import MeasurementRecord
from metrology_process_planner.domains.session import (
    CaptureGeometry,
    CaptureRecord,
    GridDatasetRecord,
    ProcessContext,
    ProcessOutputRecord,
    ReportRecord,
    SessionMode,
    SessionRecord,
)
from metrology_process_planner.persistence.csv_export import CaptureCsvExporter
from metrology_process_planner.persistence.json_store import SessionJsonStore
from metrology_process_planner.persistence.paths import SessionPaths
from tests.artifact_helpers import capture_crop_artifact


class CanonicalSessionJsonTests(unittest.TestCase):
    def test_session_json_writes_v5_top_level_sections_and_registry_refs(self) -> None:
        payload = _session().to_dict()

        self.assertEqual("5.0.0", payload["schema"]["version"])
        self.assertEqual(
            {
                "schema",
                "session",
                "paths",
                "source_layout",
                "coordinates",
                "setup",
                "captures",
                "grid_datasets",
                "process_context",
                "process_outputs",
                "reports",
                "artifacts",
                "warnings",
                "workflow",
                "extensions",
                "audit",
            },
            set(payload),
        )
        self.assertIn("capture-cap-001-crop", payload["artifacts"])
        self.assertEqual(
            {"crop": "capture-cap-001-crop"},
            payload["captures"][0]["artifact_refs"],
        )
        active_context = payload["process_context"]["active"]
        self.assertEqual("recipe-001", active_context["recipe"]["recipe_id"])
        self.assertEqual("fixture", active_context["solver"]["backend"])
        self.assertNotIn("images", payload["captures"][0])

    def test_process_grid_and_report_records_round_trip_from_v5_json(self) -> None:
        loaded = SessionRecord.from_dict(_session().to_dict())

        self.assertEqual("recipe-001", loaded.process_context.recipe_id)
        self.assertEqual("grid-001", loaded.grid_datasets[0].id)
        self.assertEqual("meas-grid-001", loaded.grid_datasets[0].measurements[0].id)
        self.assertEqual("stack-output", loaded.process_outputs[0].output_type)
        self.assertEqual("summary", loaded.reports[0].report_type)

    def test_flat_legacy_process_context_migrates_into_active_context_model(self) -> None:
        payload = {
            "schema_version": 4,
            "id": "session-legacy",
            "name": "Legacy",
            "mode": "process_aware_metrology",
            "created_at": "2026-06-23T20:00:00Z",
            "updated_at": "2026-06-23T20:00:00Z",
            "captures": [],
            "process_context": {
                "recipe_id": "legacy-recipe",
                "solver_backend": "legacy-solver",
            },
        }

        loaded = SessionRecord.from_dict(payload)

        self.assertEqual("legacy-recipe", loaded.process_context.recipe_id)
        self.assertEqual("legacy-solver", loaded.process_context.solver_backend)

    def test_json_store_writes_backup_and_csv_regenerates_from_v5_json(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            paths = SessionPaths.for_folder(Path(temp_dir))
            store = SessionJsonStore()
            store.save(_session(), paths)
            (paths.folder / "images" / "cap-001.png").write_bytes(b"fake")
            store.save(store.load(paths.folder), paths)
            loaded = store.load(paths.folder)
            csv_path = CaptureCsvExporter().export(loaded, paths.capture_csv)
            raw = json.loads(paths.session_json.read_text(encoding="utf-8"))
            backup_exists = paths.session_json.with_suffix(".json.bak").exists()
            csv_text = csv_path.read_text(encoding="utf-8")

        self.assertTrue(backup_exists)
        self.assertEqual("5.0.0", raw["schema"]["version"])
        self.assertIn("images/cap-001.png", csv_text)


def _session() -> SessionRecord:
    measurement = MeasurementRecord(
        "meas-001",
        "Gate CD",
        Point(1, 1),
        Point(3, 1),
    )
    grid_measurement = MeasurementRecord(
        "meas-grid-001",
        "Grid CD",
        Point(0, 0),
        Point(1, 0),
    )
    capture = CaptureRecord(
        id="cap-001",
        label="Site 1",
        geometry=CaptureGeometry.box(Box(0, 0, 5, 5)),
        created_at="2026-06-23T20:00:00Z",
        artifact_refs={"crop": "capture-cap-001-crop"},
        measurements=(measurement,),
    )
    return SessionRecord(
        id="session-001",
        name="Canonical Demo",
        mode=SessionMode.PROCESS_AWARE_METROLOGY,
        created_at="2026-06-23T20:00:00Z",
        updated_at="2026-06-23T20:00:00Z",
        captures=(capture,),
        artifacts={"capture-cap-001-crop": capture_crop_artifact()},
        grid_datasets=(
            GridDatasetRecord(
                "grid-001",
                "Grid",
                capture_ids=("cap-001",),
                measurements=(grid_measurement,),
            ),
        ),
        process_context=ProcessContext(
            recipe_id="recipe-001",
            recipe_name="Demo Recipe",
            recipe_snapshot_policy="embed_minimal_summary",
            solver_backend="fixture",
            solver_version="1",
        ),
        process_outputs=(
            ProcessOutputRecord("process-output-001", "Stack", "stack-output"),
        ),
        reports=(ReportRecord("report-001", "Summary", "summary"),),
    )


if __name__ == "__main__":
    unittest.main()
