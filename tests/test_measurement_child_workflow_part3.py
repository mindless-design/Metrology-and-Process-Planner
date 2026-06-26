"""Characterization tests for saved-capture child measurement workflow."""

from __future__ import annotations

import unittest
from dataclasses import replace

from metrology_process_planner.domains.geometry import Point
from metrology_process_planner.domains.session import (
    ArtifactDependencyRef,
    ArtifactOwnerRef,
    ArtifactRecord,
    ArtifactRepairMetadata,
    ArtifactStatus,
    ModeDefinition,
    ModeRegistry,
    SessionMode,
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


class MeasurementChildWorkflowTestsPart3(unittest.TestCase):
    def test_loaded_recipe_free_override_ignores_hidden_measurement_detail_ref(self) -> None:
        source = replace(saved_capture_session(), mode=SessionMode.PROFILOMETRY_PLANNER)
        pending = add_pending_measurement_line(
            source,
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
        registry = _recipe_free_registry_for(source.mode.value)

        saved = save_pending_measurements(pending, registry)

        measurement = saved.captures[0].measurements[0]
        artifact_id = measurement.artifact_refs["measurement_detail"]
        artifact = saved.artifacts[artifact_id]
        self.assertNotEqual(hidden.id, artifact_id)
        self.assertEqual("measurement_detail", artifact.type)
        self.assertEqual("measurement_detail", artifact.owner.role)
        self.assertEqual(ArtifactStatus.PENDING, artifact.status)
        self.assertEqual(ArtifactStatus.MISSING, saved.artifacts[hidden.id].status)

    def test_loaded_recipe_free_override_keeps_hidden_process_export_current(self) -> None:
        visible = ArtifactRecord(
            "summary-csv",
            "csv",
            "Capture CSV",
            "exports/session_summary.csv",
            ArtifactOwnerRef("session", "session-001", "csv"),
            status=ArtifactStatus.PRESENT,
        )
        hidden = ArtifactRecord(
            "legacy-process-csv",
            "process_output",
            "Legacy Process Export",
            "process_outputs/legacy.csv",
            ArtifactOwnerRef("process_output", "legacy-stack", "csv"),
            status=ArtifactStatus.PRESENT,
            dependencies=(ArtifactDependencyRef(kind="capture", id="cap-001"),),
        )
        source = replace(
            saved_capture_session(),
            mode=SessionMode.PROFILOMETRY_PLANNER,
            artifacts={visible.id: visible, hidden.id: hidden},
        )
        pending = add_pending_measurement_line(
            source,
            "canvas-cap",
            Point(1, 1),
            Point(4, 1),
        )
        registry = _recipe_free_registry_for(source.mode.value)

        saved = save_pending_measurements(pending, registry)

        self.assertEqual(ArtifactStatus.STALE, saved.artifacts[visible.id].status)
        self.assertEqual(
            "measurement added",
            saved.artifacts[visible.id].extensions["stale_reason"],
        )
        self.assertEqual(ArtifactStatus.PRESENT, saved.artifacts[hidden.id].status)
        self.assertNotIn("stale_reason", saved.artifacts[hidden.id].extensions)
