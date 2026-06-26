import unittest

from metrology_process_planner.reporting.readiness import ReadinessStatus, ReportReadiness
from metrology_process_planner.ui.reporting_workbench.actions import (
    primary_action_id,
    workbench_actions,
)


class ReportingWorkbenchStaleActionTests(unittest.TestCase):
    def test_stale_outputs_make_regenerate_stale_primary(self) -> None:
        readiness = ReportReadiness(ReadinessStatus.STALE_OUTPUTS)

        actions = workbench_actions(readiness)
        by_id = {action.action_id: action for action in actions}

        self.assertEqual("regenerate_stale", primary_action_id(readiness))
        self.assertEqual("regenerate_stale", by_id["regenerate_stale"].primary_action_id)
        self.assertEqual("regenerate_stale", by_id["regenerate_missing"].primary_action_id)


if __name__ == "__main__":
    unittest.main()
