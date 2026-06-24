import tempfile
import unittest
from pathlib import Path

from metrology_process_planner.domains.geometry import Box, Point
from metrology_process_planner.domains.measurements import MeasurementRecord
from metrology_process_planner.domains.session import (
    CaptureGeometry,
    CaptureRecord,
    SessionMode,
    SessionRecord,
    utc_now_iso,
)
from metrology_process_planner.persistence.csv_export import CaptureCsvExporter
from metrology_process_planner.persistence.json_store import SessionJsonStore
from metrology_process_planner.persistence.paths import SessionPaths
from tests.artifact_helpers import capture_crop_artifact


class SessionRoundTripTests(unittest.TestCase):
    def test_session_json_round_trip_preserves_capture_and_measurement(self) -> None:
        session = _sample_session()

        with tempfile.TemporaryDirectory() as temp_dir:
            paths = SessionPaths.for_folder(Path(temp_dir))
            store = SessionJsonStore()
            store.save(session, paths)
            loaded = store.load(paths.folder)

        self.assertEqual("5.0.0", loaded.schema_version)
        self.assertEqual(session.id, loaded.id)
        self.assertEqual(session.captures[0].id, loaded.captures[0].id)
        self.assertEqual(
            session.captures[0].measurements[0].id,
            loaded.captures[0].measurements[0].id,
        )
        self.assertIn("capture-cap-001-crop", loaded.artifacts)
        self.assertTrue(any(warning.code == "artifact_missing" for warning in loaded.warnings))

    def test_capture_csv_export_contains_summary_row(self) -> None:
        session = _sample_session()

        with tempfile.TemporaryDirectory() as temp_dir:
            destination = Path(temp_dir) / "captures.csv"
            CaptureCsvExporter().export(session, destination)
            csv_text = destination.read_text(encoding="utf-8")

        self.assertIn("capture_id", csv_text)
        self.assertIn("cap-001", csv_text)
        self.assertIn("images/cap-001.png", csv_text)


def _sample_session() -> SessionRecord:
    now = utc_now_iso()
    measurement = MeasurementRecord(
        id="meas-001",
        label="Gate CD",
        start=Point(1, 1),
        end=Point(3, 1),
        target=2.0,
        lower_spec_limit=1.8,
        upper_spec_limit=2.2,
    )
    capture = CaptureRecord(
        id="cap-001",
        label="Site 1",
        geometry=CaptureGeometry.box(Box(0, 0, 5, 5)),
        created_at=now,
        notes="Initial capture",
        measurements=(measurement,),
    )
    return SessionRecord(
        id="session-001",
        name="Demo Session",
        mode=SessionMode.SIMPLE_CAPTURE,
        created_at=now,
        updated_at=now,
        captures=(capture,),
        artifacts={"capture-cap-001-crop": capture_crop_artifact()},
    )


if __name__ == "__main__":
    unittest.main()
