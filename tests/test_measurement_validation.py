import unittest
from dataclasses import replace

from metrology_process_planner.domains.geometry import Box, Point
from metrology_process_planner.domains.measurement.records import MeasurementRecord
from metrology_process_planner.workflows.measurement_validation import measurement_validation_errors
from metrology_process_planner.workflows.measurement_workflow import add_pending_measurement_line
from tests.measurement_child_fixtures import saved_capture_session


class MeasurementValidationTests(unittest.TestCase):
    def test_measurement_inside_capture_bounds_has_no_warning(self) -> None:
        measurement = MeasurementRecord(
            id="m1",
            label="CD",
            start=Point(1, 1),
            end=Point(4, 1),
            target=3.0,
            lower_spec_limit=2.5,
            upper_spec_limit=3.5,
        )

        warnings = measurement.validate_against_capture_bounds(Box(0, 0, 5, 5))

        self.assertEqual((), warnings)

    def test_measurement_outside_capture_bounds_is_reported(self) -> None:
        measurement = MeasurementRecord(
            id="m1",
            label="CD",
            start=Point(1, 1),
            end=Point(6, 1),
        )

        warnings = measurement.validate_against_capture_bounds(Box(0, 0, 5, 5))

        self.assertIn("Measurement line is outside the parent capture bounds.", warnings)

    def test_zero_length_measurement_is_reported(self) -> None:
        measurement = MeasurementRecord(
            id="m1",
            label="CD",
            start=Point(1, 1),
            end=Point(1, 1),
        )

        warnings = measurement.validate_against_capture_bounds(Box(0, 0, 5, 5))

        self.assertIn("Measurement line length must be greater than zero.", warnings)

    def test_spec_limits_must_contain_target(self) -> None:
        measurement = MeasurementRecord(
            id="m1",
            label="CD",
            start=Point(1, 1),
            end=Point(4, 1),
            target=6.0,
            lower_spec_limit=2.5,
            upper_spec_limit=3.5,
        )

        warnings = measurement.validate_against_capture_bounds(Box(0, 0, 5, 5))

        self.assertIn("Target is above upper spec limit.", warnings)

    def test_session_measurement_validation_reports_parent_context(self) -> None:
        source = saved_capture_session()
        capture = source.captures[0]
        invalid = MeasurementRecord("meas-001", "CD", Point(1, 1), Point(6, 1))
        source = replace(source, captures=(capture.add_measurement(invalid),))

        errors = measurement_validation_errors(source)

        self.assertEqual(
            ("meas-001: Measurement line is outside the parent capture bounds.",),
            errors,
        )

    def test_pending_measurement_requires_existing_parent_capture(self) -> None:
        source = replace(saved_capture_session(), captures=())

        with self.assertRaisesRegex(ValueError, "existing parent capture"):
            add_pending_measurement_line(source, "canvas-cap", Point(1, 1), Point(4, 1))


if __name__ == "__main__":
    unittest.main()
