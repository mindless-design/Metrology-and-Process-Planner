import unittest
from dataclasses import replace

from metrology_process_planner.domains.geometry import Point
from metrology_process_planner.domains.measurements import MeasurementRecord
from metrology_process_planner.domains.session import (
    ArtifactStatus,
    CanvasObjectType,
    ProcessContext,
    WorkflowState,
)
from metrology_process_planner.workflows import (
    ArtifactRepairStateMachine,
    CaptureInteractionStateMachine,
    InteractionContext,
    MeasurementWorkflowStateMachine,
    PendingReviewStateMachine,
    RecipeContextStateMachine,
    SessionUIStateMachine,
)
from tests.editor_render_fixtures import session, session_without_pending


class UiStateMachineTests(unittest.TestCase):
    def test_session_state_reports_pending_review(self) -> None:
        snapshot = SessionUIStateMachine().evaluate(session())

        self.assertEqual("session_ui", snapshot.machine)
        self.assertEqual("pending_review", snapshot.state)
        self.assertEqual("pending:pending-001", snapshot.active_item_ref)
        self.assertIn("SavePendingCapture", snapshot.action_ids)

    def test_capture_state_reports_armed_and_dragging(self) -> None:
        armed = InteractionContext(armed_object_type=CanvasObjectType.SITE_BOX)
        dragging = InteractionContext(
            armed_object_type=CanvasObjectType.SITE_BOX,
            live_preview_id="canvas-live",
            drag_start=Point(0, 0),
        )

        self.assertEqual("armed_box", CaptureInteractionStateMachine().evaluate(armed).state)
        self.assertEqual(
            "dragging_preview",
            CaptureInteractionStateMachine().evaluate(dragging).state,
        )

    def test_pending_review_actions_distinguish_child_capture(self) -> None:
        current = session()
        child = replace(current.pending_captures[0], parent_id="canvas-parent")
        current = replace(current, pending_captures=(child,))

        snapshot = PendingReviewStateMachine().evaluate(current)

        self.assertEqual("pending_review", snapshot.state)
        self.assertIn("SaveCompositeCapture", snapshot.action_ids)
        self.assertIn("RetakeInnerFeature", snapshot.action_ids)

    def test_measurement_state_reports_pending_measurement_actions(self) -> None:
        current = session_without_pending()
        capture = current.captures[0]
        measurement = MeasurementRecord(
            "meas-pending",
            "Pending",
            Point(1, 1),
            Point(2, 2),
            metadata={"workflow_state": "pending"},
        )
        current = replace(
            current,
            captures=(replace(capture, measurements=(measurement,)),),
        )

        snapshot = MeasurementWorkflowStateMachine().evaluate(current)

        self.assertEqual("pending_measurement", snapshot.state)
        self.assertEqual("measurement:meas-pending", snapshot.active_item_ref)
        self.assertEqual(
            ("SaveMeasurement", "RetakeMeasurementLine", "DiscardMeasurement"),
            snapshot.action_ids,
        )

    def test_recipe_and_artifact_repair_states_are_visible(self) -> None:
        current = session_without_pending()
        artifact_id, artifact = next(iter((current.artifacts or {}).items()))
        current = replace(
            current,
            process_context=ProcessContext(recipe_id="recipe-001", warning_ids=("warn-recipe",)),
            artifacts={
                artifact_id: replace(
                    artifact,
                    status=ArtifactStatus.MISSING,
                    warning_ids=("warn-artifact",),
                )
            },
        )

        recipe = RecipeContextStateMachine().evaluate(current)
        repair = ArtifactRepairStateMachine().evaluate(current)

        self.assertEqual("warning", recipe.state)
        self.assertEqual(("warn-recipe",), recipe.warning_ids)
        self.assertEqual("open_tasks", repair.state)
        self.assertEqual(("warn-artifact",), repair.warning_ids)

    def test_session_workflow_state_reports_active_resume_data(self) -> None:
        current = replace(
            session_without_pending(),
            workflow=WorkflowState(
                active=True,
                stage="measurement_line",
                pending_item_ref="capture:cap-001",
            ),
        )

        session_snapshot = SessionUIStateMachine().evaluate(current)
        measurement_snapshot = MeasurementWorkflowStateMachine().evaluate(current)

        self.assertEqual("measurement_line", session_snapshot.state)
        self.assertEqual("armed_line", measurement_snapshot.state)


if __name__ == "__main__":
    unittest.main()
