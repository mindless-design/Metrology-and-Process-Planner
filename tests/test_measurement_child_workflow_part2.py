"""Characterization tests for saved-capture child measurement workflow."""

from __future__ import annotations

import unittest
from dataclasses import replace

from metrology_process_planner.domains.geometry import Point
from metrology_process_planner.domains.session import (
    ArtifactOwnerRef,
    ArtifactRecord,
    ArtifactRepairMetadata,
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


class MeasurementChildWorkflowTestsPart2(unittest.TestCase):
    def test_pending_measurement_save_creates_measurement_detail_placeholder(self) -> None:
        pending = add_pending_measurement_line(
            saved_capture_session(),
            "canvas-cap",
            Point(1, 1),
            Point(4, 1),
        )

        saved = save_pending_measurements(pending)

        measurement = saved.captures[0].measurements[0]
        artifact_id = measurement.artifact_refs["measurement_detail"]
        artifact = saved.artifacts[artifact_id]
        self.assertEqual(measurement.artifact_refs["annotation"], artifact_id)
        self.assertEqual("measurement_detail", artifact.type)
        self.assertEqual("measurement_detail", artifact.owner.role)
        self.assertEqual("pending", artifact.status.value)
        self.assertEqual((f"warning-{artifact_id}-pending",), artifact.warning_ids)

    def test_hidden_process_measurement_detail_ref_does_not_block_placeholder(self) -> None:
        pending = add_pending_measurement_line(
            saved_capture_session(),
            "canvas-cap",
            Point(1, 1),
            Point(4, 1),
        )
        pending_measurement = pending.captures[0].measurements[0]
        hidden = ArtifactRecord(
            "legacy-measurement-process-output",
            "process_output",
            "Legacy Measurement Process Output",
            "process_outputs/meas-001-stack.png",
            ArtifactOwnerRef("measurement", "meas-001", "measurement_detail"),
            status=ArtifactStatus.MISSING,
            repair=ArtifactRepairMetadata(
                repair_action="regenerate_process_output",
                requires_recipe=True,
                requires_solver=True,
            ),
        )
        pending_measurement = replace(
            pending_measurement,
            artifact_refs={"measurement_detail": hidden.id},
        )
        pending_capture = replace(pending.captures[0], measurements=(pending_measurement,))
        pending = replace(
            pending,
            captures=(pending_capture,),
            artifacts={hidden.id: hidden},
        )

        saved = save_pending_measurements(pending)

        measurement = saved.captures[0].measurements[0]
        artifact_id = measurement.artifact_refs["measurement_detail"]
        artifact = saved.artifacts[artifact_id]
        self.assertNotEqual(hidden.id, artifact_id)
        self.assertEqual("measurement_detail", artifact.type)
        self.assertEqual("measurement_detail", artifact.owner.role)
        self.assertEqual(ArtifactStatus.PENDING, artifact.status)
        self.assertEqual(ArtifactStatus.MISSING, saved.artifacts[hidden.id].status)
