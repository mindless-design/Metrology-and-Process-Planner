"""Characterization tests for saved-capture child measurement workflow."""

from __future__ import annotations

import unittest
from dataclasses import replace

from metrology_process_planner.domains.geometry import Point
from metrology_process_planner.domains.session import (
    ArtifactStatus,
    ModeDefinition,
    ModeRegistry,
)
from metrology_process_planner.workflows.measurement_workflow import (
    add_pending_measurement_line,
    save_pending_measurements,
)
from tests.measurement_child_fixtures import (
    saved_capture_session,
)


def _recipe_free_registry_for(mode_id: str) -> ModeRegistry:
    return ModeRegistry((ModeDefinition(mode_id, "Recipe Free Override"),))

if __name__ == "__main__":
    unittest.main()


class MeasurementChildWorkflowTestsPart4(unittest.TestCase):
    def test_saving_later_measurement_does_not_reset_existing_detail_artifact(self) -> None:
        first_saved = save_pending_measurements(
            add_pending_measurement_line(
                saved_capture_session(),
                "canvas-cap",
                Point(1, 1),
                Point(4, 1),
            )
        )
        first_measurement = first_saved.captures[0].measurements[0]
        first_artifact_id = first_measurement.artifact_refs["measurement_detail"]
        artifacts = dict(first_saved.artifacts or {})
        artifacts[first_artifact_id] = replace(
            artifacts[first_artifact_id],
            status=ArtifactStatus.PRESENT,
            warning_ids=(),
        )
        first_measurement = replace(first_measurement, warning_ids=())
        first_capture = replace(first_saved.captures[0], measurements=(first_measurement,))
        first_saved = replace(
            first_saved,
            captures=(first_capture,),
            artifacts=artifacts,
            warnings=(),
        )

        second_pending = add_pending_measurement_line(
            first_saved,
            "canvas-cap",
            Point(1, 2),
            Point(4, 2),
        )
        saved = save_pending_measurements(second_pending)

        first_after = saved.captures[0].measurements[0]
        second_after = saved.captures[0].measurements[1]
        self.assertEqual(first_artifact_id, first_after.artifact_refs["measurement_detail"])
        self.assertEqual(ArtifactStatus.PRESENT, saved.artifacts[first_artifact_id].status)
        self.assertEqual((), saved.artifacts[first_artifact_id].warning_ids)
        self.assertEqual((), first_after.warning_ids)
        self.assertEqual("meas-002", second_after.id)
        self.assertEqual(
            ArtifactStatus.PENDING,
            saved.artifacts[second_after.artifact_refs["measurement_detail"]].status,
        )
