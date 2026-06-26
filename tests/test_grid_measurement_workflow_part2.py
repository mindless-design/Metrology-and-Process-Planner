import unittest
from dataclasses import replace

from metrology_process_planner.domains.geometry import Box
from metrology_process_planner.domains.session import (
    CaptureGeometry,
    CaptureRecord,
    SessionMode,
    SessionRecord,
)
from metrology_process_planner.workflows.editor import (
    DefaultSessionModeAdapter,
    EditorAction,
    EditorActionDispatcher,
    EditorActionType,
    SessionDocumentBuilder,
)
from metrology_process_planner.workflows.grid_measurement import create_grid_dataset

_CREATED_AT = "2026-06-24T00:00:00Z"


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
    return CaptureRecord(capture_id, capture_id, CaptureGeometry.box(bounds), _CREATED_AT)

if __name__ == "__main__":
    unittest.main()


class GridMeasurementWorkflowTestsPart2(unittest.TestCase):
    def test_invalid_grid_geometry_creates_structured_warning_without_dataset(self) -> None:
        session = create_grid_dataset(_session(overlap=True), "cap-a", "cap-b", 2, 2)

        self.assertEqual((), session.grid_datasets)
        warning = session.warnings[0]
        self.assertEqual("GRID_GEOMETRY_INVALID", warning.code)
        self.assertEqual(("capture:cap-a", "capture:cap-b"), warning.related_item_refs)

    def test_invalid_grid_dimensions_create_structured_warning_without_dataset(self) -> None:
        session = create_grid_dataset(_session(), "cap-a", "cap-b", 0, 2)

        self.assertEqual((), session.grid_datasets)
        warning = session.warnings[0]
        self.assertEqual("GRID_SIZE_INVALID", warning.code)
        self.assertEqual(("capture:cap-a", "capture:cap-b"), warning.related_item_refs)

    def test_dashboard_exposes_grid_dataset_creation_action(self) -> None:
        document = SessionDocumentBuilder().build(_session())
        actions = DefaultSessionModeAdapter().actions(
            document.session,
            document.items_by_id["dashboard"],
        )

        self.assertIn("Create Grid Dataset", [action.label for action in actions])
        self.assertIn(
            EditorActionType.CREATE_GRID_DATASET,
            [action.action_type for action in actions],
        )

    def test_dashboard_disables_grid_dataset_creation_without_two_box_anchors(self) -> None:
        source = _session()
        document = SessionDocumentBuilder().build(replace(source, captures=source.captures[:1]))
        actions = DefaultSessionModeAdapter().actions(
            document.session,
            document.items_by_id["dashboard"],
        )

        create_grid = next(
            action
            for action in actions
            if action.action_type is EditorActionType.CREATE_GRID_DATASET
        )

        self.assertFalse(create_grid.enabled)
        self.assertEqual(
            "Grid datasets require at least two saved box captures.",
            create_grid.disabled_reason,
        )

        result = EditorActionDispatcher().dispatch(document, create_grid)

        self.assertEqual("unavailable", result.status)
        self.assertEqual(create_grid.disabled_reason, result.message)

    def test_grid_dataset_creation_action_creates_and_selects_dataset(self) -> None:
        document = SessionDocumentBuilder().build(_session())
        action = EditorAction(
            EditorActionType.CREATE_GRID_DATASET,
            "Create Grid Dataset",
            "dashboard",
            payload=(
                ("first_anchor_capture_id", "cap-a"),
                ("diagonal_anchor_capture_id", "cap-b"),
                ("row_count", "2"),
                ("column_count", "3"),
                ("label", "Gate grid"),
            ),
        )

        result = EditorActionDispatcher().dispatch(document, action)

        self.assertEqual("success", result.status)
        self.assertEqual("grid:grid-001", result.document.selection.selected_item_id)
        self.assertEqual(1, len(result.document.session.grid_datasets))
        grid_item = result.document.items_by_id["grid:grid-001"]
        previews = DefaultSessionModeAdapter().preview_options(result.document.session, grid_item)
        self.assertEqual("Grid Overview", previews[0].label)
        self.assertEqual("placeholder", previews[0].status)
        self.assertIn("Generate grid overview", previews[0].placeholder)
        self.assertEqual(
            6,
            result.document.session.grid_datasets[0].metadata["planned_site_count"],
        )

    def test_dashboard_grid_dataset_action_is_directly_routable(self) -> None:
        document = SessionDocumentBuilder().build(_session())
        action = next(
            action
            for action in DefaultSessionModeAdapter().actions(
                document.session,
                document.items_by_id["dashboard"],
            )
            if action.action_type is EditorActionType.CREATE_GRID_DATASET
        )

        result = EditorActionDispatcher().dispatch(document, action)

        self.assertEqual("success", result.status)
        self.assertEqual("grid:grid-001", result.document.selection.selected_item_id)
        self.assertEqual(1, result.document.session.grid_datasets[0].metadata["planned_site_count"])
        self.assertEqual(
            ("cap-a", "cap-b"),
            result.document.session.grid_datasets[0].metadata["anchor_capture_ids"],
        )

    def test_grid_dataset_creation_action_reports_validation_warning(self) -> None:
        document = SessionDocumentBuilder().build(_session(overlap=True))
        action = EditorAction(
            EditorActionType.CREATE_GRID_DATASET,
            "Create Grid Dataset",
            "dashboard",
            payload=(
                ("first_anchor_capture_id", "cap-a"),
                ("diagonal_anchor_capture_id", "cap-b"),
                ("row_count", "2"),
                ("column_count", "2"),
            ),
        )

        result = EditorActionDispatcher().dispatch(document, action)

        self.assertEqual("warning", result.status)
        self.assertIn("GRID_GEOMETRY_INVALID", result.message)
        self.assertIn("Grid anchors must not overlap exactly", result.message)
        self.assertEqual((), result.document.session.grid_datasets)

    def test_grid_dataset_creation_action_requires_payload(self) -> None:
        document = SessionDocumentBuilder().build(_session())

        result = EditorActionDispatcher().dispatch(
            document,
            EditorAction(EditorActionType.CREATE_GRID_DATASET, "Create Grid Dataset", "dashboard"),
        )

        self.assertEqual("unavailable", result.status)
        self.assertIn("requires two anchor capture IDs", result.message)
