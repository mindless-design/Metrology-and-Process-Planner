import unittest
from pathlib import Path
from tempfile import TemporaryDirectory

from metrology_process_planner.domains.geometry import Box
from metrology_process_planner.domains.session import (
    ArtifactStatus,
    CaptureGeometry,
    CaptureRecord,
    SessionMode,
    SessionRecord,
)
from metrology_process_planner.persistence.paths import SessionPaths
from metrology_process_planner.workflows.editor import (
    DefaultSessionModeAdapter,
    EditorActionDispatcher,
    EditorActionType,
    SessionDocumentBuilder,
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


class GridMeasurementWorkflowTestsPart1(unittest.TestCase):
    def test_grid_dataset_creates_site_list_and_overview_placeholder(self) -> None:
        session = create_grid_dataset(_session(), "cap-a", "cap-b", 2, 3, "Gate grid")

        dataset = session.grid_datasets[0]
        artifact_id = dataset.artifact_refs["grid_overview"]
        planned_sites = dataset.extensions["planned_sites"]

        self.assertEqual("Gate grid", dataset.label)
        self.assertEqual(("cap-a", "cap-b"), dataset.capture_ids)
        self.assertEqual(6, dataset.metadata["planned_site_count"])
        self.assertEqual("grid-001:site-001", dataset.metadata["first_planned_site_id"])
        self.assertEqual("grid-001:site-006", dataset.metadata["last_planned_site_id"])
        self.assertEqual(6, len(planned_sites))
        self.assertEqual("grid-001:site-001", planned_sites[0]["id"])
        self.assertEqual("Gate grid R01C01", planned_sites[0]["label"])
        self.assertEqual({"x": 5.0, "y": 5.0}, planned_sites[0]["center"])
        self.assertEqual("grid-001:site-006", planned_sites[-1]["id"])
        self.assertEqual("Gate grid R02C03", planned_sites[-1]["label"])
        self.assertEqual({"x": 25.0, "y": 25.0}, planned_sites[-1]["center"])
        self.assertEqual("grid_overview", session.artifacts[artifact_id].owner.role)
        self.assertEqual("placeholder", session.artifacts[artifact_id].status.value)
        self.assertEqual((session.warnings[0].id,), session.artifacts[artifact_id].warning_ids)
        self.assertEqual((session.warnings[0].id,), dataset.warning_ids)
        self.assertEqual("GRID_OVERVIEW_PLACEHOLDER", session.warnings[0].code)

    def test_grid_dataset_appears_in_editor_group(self) -> None:
        session = create_grid_dataset(_session(), "cap-a", "cap-b", 2, 2)

        document = SessionDocumentBuilder().build(session)

        self.assertIn("grid:grid-001", document.items_by_id)
        self.assertIn(
            "Grid Datasets",
            [group.label for group in document.navigator_groups],
        )
        self.assertEqual(
            "grid_dataset",
            document.items_by_id["grid:grid-001"].role,
        )
        self.assertIn("warning:warning-grid-overview-grid-001-placeholder", document.items_by_id)

    def test_grid_dataset_inspector_shows_planning_summary(self) -> None:
        session = create_grid_dataset(_session(), "cap-a", "cap-b", 2, 3, "Gate grid")
        document = SessionDocumentBuilder().build(session)
        grid_item = document.items_by_id["grid:grid-001"]

        fields = DefaultSessionModeAdapter().metadata_fields(session, grid_item)

        values = {field.key: field.value for field in fields}
        self.assertEqual("Gate grid", values["label"])
        self.assertEqual("cap-a, cap-b", values["anchor_capture_ids"])
        self.assertEqual("2", values["row_count"])
        self.assertEqual("3", values["column_count"])
        self.assertEqual("6", values["planned_site_count"])
        self.assertEqual("grid-001:site-001", values["first_planned_site_id"])
        self.assertEqual("grid-001:site-006", values["last_planned_site_id"])
        self.assertEqual("placeholder", values["grid_overview_status"])

    def test_grid_dataset_placeholder_preview_is_repairable(self) -> None:
        session = create_grid_dataset(_session(), "cap-a", "cap-b", 2, 2)
        document = SessionDocumentBuilder().build(session)
        grid_item = document.items_by_id["grid:grid-001"]
        adapter = DefaultSessionModeAdapter()

        previews = adapter.preview_options(session, grid_item)
        actions = adapter.actions(session, grid_item)

        self.assertEqual("placeholder", previews[0].status)
        self.assertIn("Grid overview artifact is a placeholder", previews[0].placeholder)
        self.assertIn("Repair: Generate grid overview.", previews[0].placeholder)
        self.assertIn("Regenerate Grid Overview", [action.label for action in actions])

    def test_grid_dataset_regenerate_action_repairs_placeholder_overview(self) -> None:
        session = create_grid_dataset(_session(), "cap-a", "cap-b", 2, 2)
        document = SessionDocumentBuilder().build(session)
        grid_item = document.items_by_id["grid:grid-001"]
        action = next(
            item
            for item in DefaultSessionModeAdapter().actions(session, grid_item)
            if item.action_type is EditorActionType.REGENERATE_ARTIFACT
        )

        with TemporaryDirectory() as temp_dir:
            paths = SessionPaths.for_folder(Path(temp_dir))
            paths.ensure_created()
            result = EditorActionDispatcher(paths=paths).dispatch(document, action)

            artifact_id = result.document.session.grid_datasets[0].artifact_refs["grid_overview"]
            artifact = result.document.session.artifacts[artifact_id]

            self.assertEqual("success", result.status)
            self.assertEqual(ArtifactStatus.PRESENT, artifact.status)
            self.assertEqual((), artifact.warning_ids)
            self.assertEqual((), result.document.session.grid_datasets[0].warning_ids)
            self.assertNotIn(
                "GRID_OVERVIEW_PLACEHOLDER",
                {warning.code for warning in result.document.session.warnings},
            )
            self.assertTrue((paths.folder / artifact.relative_path).exists())
