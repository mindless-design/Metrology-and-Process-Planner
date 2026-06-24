import unittest

from metrology_process_planner.domains.geometry import Box, Point
from metrology_process_planner.domains.measurements import MeasurementRecord


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


if __name__ == "__main__":
    unittest.main()

