import tempfile
import unittest
from dataclasses import replace
from pathlib import Path

from metrology_process_planner.domains.geometry import Point
from metrology_process_planner.persistence.paths import SessionPaths
from metrology_process_planner.workflows.editor import (
    EditorAction,
    EditorActionDispatcher,
    EditorActionType,
    mark_metadata_edit,
)
from tests.measurement_child_fixtures import saved_measurement_document


def _with_measurement_line(document, start: Point, end: Point):
    session = document.session
    capture = session.captures[0]
    measurement = replace(capture.measurements[0], start=start, end=end)
    capture = replace(capture, measurements=(measurement,))
    return replace(document, session=replace(session, captures=(capture,)))

if __name__ == "__main__":
    unittest.main()


class MeasurementSaveValidationTestsPart2(unittest.TestCase):
    def test_optional_measurement_specs_can_be_cleared_on_save(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            paths = SessionPaths.for_folder(Path(temp_dir))
            paths.ensure_created()
            document = saved_measurement_document(paths)
            document = mark_metadata_edit(document, "measurement:meas-001", "target", "")
            document = mark_metadata_edit(document, "measurement:meas-001", "lower_spec_limit", "")
            document = mark_metadata_edit(document, "measurement:meas-001", "upper_spec_limit", "")

            result = EditorActionDispatcher(paths=paths).dispatch(
                document,
                EditorAction(EditorActionType.SAVE_EDITS, "Save"),
            )

        measurement = result.document.session.captures[0].measurements[0]
        self.assertIn(result.status, {"success", "warning"})
        self.assertIsNone(measurement.target)
        self.assertIsNone(measurement.lower_spec_limit)
        self.assertIsNone(measurement.upper_spec_limit)
        self.assertGreater(measurement.line_weight, 0)

    def test_invalid_measurement_number_edit_blocks_save(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            paths = SessionPaths.for_folder(Path(temp_dir))
            paths.ensure_created()
            document = saved_measurement_document(paths)
            document = mark_metadata_edit(document, "measurement:meas-001", "target", "abc")

            result = EditorActionDispatcher(paths=paths).dispatch(
                document,
                EditorAction(EditorActionType.SAVE_EDITS, "Save"),
            )

        measurement = result.document.session.captures[0].measurements[0]
        self.assertEqual("blocked", result.status)
        self.assertIn("Target must be a number", result.message)
        self.assertEqual(3.0, measurement.target)

    def test_invalid_measurement_color_edit_blocks_save(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            paths = SessionPaths.for_folder(Path(temp_dir))
            paths.ensure_created()
            document = saved_measurement_document(paths)
            document = mark_metadata_edit(
                document,
                "measurement:meas-001",
                "annotation_color",
                "blue",
            )

            result = EditorActionDispatcher(paths=paths).dispatch(
                document,
                EditorAction(EditorActionType.SAVE_EDITS, "Save"),
            )

        measurement = result.document.session.captures[0].measurements[0]
        self.assertEqual("blocked", result.status)
        self.assertIn("Annotation color must be a hex color", result.message)
        self.assertEqual("#00aaee", measurement.annotation_color)

    def test_mode_measurement_metadata_aliases_update_record_fields(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            paths = SessionPaths.for_folder(Path(temp_dir))
            paths.ensure_created()
            document = saved_measurement_document(paths)
            document = mark_metadata_edit(
                document,
                "measurement:meas-001",
                "edge_convention",
                "inner_edges",
            )
            document = mark_metadata_edit(document, "measurement:meas-001", "color", "#1122AA")
            document = mark_metadata_edit(
                document,
                "measurement:meas-001",
                "line_weight_px",
                "6.0",
            )

            result = EditorActionDispatcher(paths=paths).dispatch(
                document,
                EditorAction(EditorActionType.SAVE_EDITS, "Save"),
            )

        measurement = result.document.session.captures[0].measurements[0]
        self.assertIn(result.status, {"success", "warning"})
        self.assertEqual("inner_edges", measurement.edge_detection_convention)
        self.assertEqual("#1122aa", measurement.annotation_color)
        self.assertEqual(6.0, measurement.line_weight)
