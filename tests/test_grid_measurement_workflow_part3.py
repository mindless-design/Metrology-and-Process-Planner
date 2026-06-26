import unittest
from dataclasses import replace

from metrology_process_planner.app.diagnostics_summary import diagnostics_summary_rows
from metrology_process_planner.domains.geometry import Box
from metrology_process_planner.domains.session import (
    ArtifactOwnerRef,
    ArtifactRecord,
    ArtifactStatus,
    CaptureGeometry,
    CaptureRecord,
    GridDatasetRecord,
    ModeDefinition,
    ModeRegistry,
    SessionMode,
    SessionModeId,
    SessionRecord,
    built_in_mode_registry,
)
from metrology_process_planner.workflows.grid_measurement import create_grid_dataset


def _session(overlap: bool = False) -> SessionRecord:
    first = _capture("cap-a", Box(0, 0, 10, 10))
    second_bounds = Box(0, 0, 10, 10) if overlap else Box(20, 20, 30, 30)
    second = _capture("cap-b", second_bounds)
    return SessionRecord(
        "session-grid",
        "Grid Demo",
        SessionMode.GRID_MEASUREMENT,
        "2026-06-24T00:00:00Z",
        "2026-06-24T00:00:00Z",
        captures=(first, second),
    )

def _capture(capture_id: str, bounds: Box) -> CaptureRecord:
    return CaptureRecord(
        capture_id,
        capture_id,
        CaptureGeometry.box(bounds),
        "2026-06-24T00:00:00Z",
    )

if __name__ == "__main__":
    unittest.main()


class GridMeasurementWorkflowTestsPart3(unittest.TestCase):
    def test_advanced_diagnostics_summarizes_grid_dataset_state(self) -> None:
        session = create_grid_dataset(_session(), "cap-a", "cap-b", 2, 3, "Gate grid")

        rows = dict(diagnostics_summary_rows(session, (), built_in_mode_registry()))

        self.assertEqual("1", rows["Grid Datasets"])
        self.assertEqual("6", rows["Grid Planned Sites"])
        self.assertEqual("placeholder:1", rows["Grid Overview Artifacts"])
        self.assertEqual("false", rows["Recipe Required"])
        self.assertEqual("none", rows["Solver Operation"])
        self.assertEqual("false", rows["Process Context Visible"])

    def test_advanced_diagnostics_hides_legacy_process_grid_overview_status(self) -> None:
        registry = ModeRegistry((ModeDefinition("external_grid", "External Grid"),))
        hidden_process = ArtifactRecord(
            "legacy-grid-stack",
            "process_output",
            "Legacy Grid Stack",
            "process_outputs/grid-stack.json",
            ArtifactOwnerRef("grid_dataset", "grid-001", "grid_overview"),
            status=ArtifactStatus.STALE,
        )
        session = replace(
            _session(),
            mode=SessionModeId("external_grid"),
            grid_datasets=(
                GridDatasetRecord(
                    "grid-001",
                    "Legacy Grid",
                    artifact_refs={"grid_overview": hidden_process.id},
                    metadata={"planned_site_count": 4},
                ),
            ),
            artifacts={hidden_process.id: hidden_process},
        )

        rows = dict(diagnostics_summary_rows(session, (), registry))

        self.assertEqual("1", rows["Grid Datasets"])
        self.assertEqual("4", rows["Grid Planned Sites"])
        self.assertEqual("missing:1", rows["Grid Overview Artifacts"])
        self.assertEqual("false", rows["Mode Process Aware"])
        self.assertEqual("none", rows["Solver Operation"])
