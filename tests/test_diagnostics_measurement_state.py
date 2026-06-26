import unittest

from metrology_process_planner.app.diagnostics_summary import diagnostics_summary_rows
from metrology_process_planner.domains.geometry import Point
from metrology_process_planner.domains.session import built_in_mode_registry
from metrology_process_planner.workflows.measurement_workflow import (
    add_pending_measurement_line,
    begin_measurement_line,
)
from tests.measurement_child_fixtures import saved_capture_session


class DiagnosticsMeasurementStateTests(unittest.TestCase):
    def test_diagnostics_reports_armed_measurement_target_and_actions(self) -> None:
        session = begin_measurement_line(saved_capture_session(), "cap-001")

        rows = dict(diagnostics_summary_rows(session, (), built_in_mode_registry()))

        self.assertEqual("armed_line", rows["Measurement Workflow"])
        self.assertEqual("capture:cap-001", rows["Measurement Workflow Target"])
        self.assertEqual("CancelCapture", rows["Measurement Workflow Actions"])

    def test_diagnostics_reports_pending_measurement_target_and_actions(self) -> None:
        session = add_pending_measurement_line(
            saved_capture_session(),
            "canvas-cap",
            Point(1, 1),
            Point(4, 1),
        )

        rows = dict(diagnostics_summary_rows(session, (), built_in_mode_registry()))

        self.assertEqual("pending_measurement", rows["Measurement Workflow"])
        self.assertEqual("measurement:meas-001", rows["Measurement Workflow Target"])
        self.assertEqual(
            "SaveMeasurement, RetakeMeasurementLine, DiscardMeasurement",
            rows["Measurement Workflow Actions"],
        )


if __name__ == "__main__":
    unittest.main()
