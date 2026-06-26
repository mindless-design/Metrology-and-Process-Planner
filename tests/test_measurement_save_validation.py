import tempfile
import unittest
from dataclasses import replace
from pathlib import Path

from metrology_process_planner.domains.geometry import Point
from metrology_process_planner.domains.session import CaptureGeometry
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


class MeasurementSaveValidationTestsPart1(unittest.TestCase):
    def test_invalid_measurement_specs_block_save(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            paths = SessionPaths.for_folder(Path(temp_dir))
            paths.ensure_created()
            document = saved_measurement_document(paths)
            document = mark_metadata_edit(document, "measurement:meas-001", "target", "10")
            document = mark_metadata_edit(document, "measurement:meas-001", "upper_spec_limit", "5")

            result = EditorActionDispatcher(paths=paths).dispatch(
                document,
                EditorAction(EditorActionType.SAVE_EDITS, "Save"),
            )

        self.assertEqual("blocked", result.status)
        self.assertIn("Target is above upper spec limit", result.message)
        measurement = result.document.session.captures[0].measurements[0]
        self.assertEqual(3.0, measurement.target)
        self.assertEqual(3.5, measurement.upper_spec_limit)

    def test_invalid_measurement_spec_order_blocks_before_applying_edits(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            paths = SessionPaths.for_folder(Path(temp_dir))
            paths.ensure_created()
            document = saved_measurement_document(paths)
            document = mark_metadata_edit(document, "measurement:meas-001", "lsl", "4")
            document = mark_metadata_edit(document, "measurement:meas-001", "usl", "2")

            result = EditorActionDispatcher(paths=paths).dispatch(
                document,
                EditorAction(EditorActionType.SAVE_EDITS, "Save"),
            )

        self.assertEqual("blocked", result.status)
        self.assertIn("Lower spec limit is greater than upper spec limit", result.message)
        measurement = result.document.session.captures[0].measurements[0]
        self.assertEqual(2.5, measurement.lower_spec_limit)
        self.assertEqual(3.5, measurement.upper_spec_limit)

    def test_measurement_outside_parent_blocks_save(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            paths = SessionPaths.for_folder(Path(temp_dir))
            paths.ensure_created()
            document = _with_measurement_line(
                saved_measurement_document(paths),
                Point(1, 1),
                Point(6, 1),
            )

            result = EditorActionDispatcher(paths=paths).dispatch(
                document,
                EditorAction(EditorActionType.SAVE_EDITS, "Save"),
            )

        self.assertEqual("blocked", result.status)
        self.assertIn("Measurement line is outside the parent capture bounds", result.message)

    def test_zero_length_measurement_line_blocks_save(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            paths = SessionPaths.for_folder(Path(temp_dir))
            paths.ensure_created()
            document = _with_measurement_line(
                saved_measurement_document(paths),
                Point(1, 1),
                Point(1, 1),
            )

            result = EditorActionDispatcher(paths=paths).dispatch(
                document,
                EditorAction(EditorActionType.SAVE_EDITS, "Save"),
            )

        self.assertEqual("blocked", result.status)
        self.assertIn("Measurement line length must be greater than zero", result.message)

    def test_measurement_without_box_parent_blocks_save(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            paths = SessionPaths.for_folder(Path(temp_dir))
            paths.ensure_created()
            document = saved_measurement_document(paths)
            session = document.session
            capture = session.captures[0]
            capture = replace(capture, geometry=CaptureGeometry.point_capture(Point(1, 1)))
            document = replace(document, session=replace(session, captures=(capture,)))

            result = EditorActionDispatcher(paths=paths).dispatch(
                document,
                EditorAction(EditorActionType.SAVE_EDITS, "Save"),
            )

        self.assertEqual("blocked", result.status)
        self.assertIn("parent capture geometry must be a box", result.message)
