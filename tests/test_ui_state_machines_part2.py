import unittest
from dataclasses import replace

from metrology_process_planner.domains.session import (
    ArtifactOwnerRef,
    ArtifactRecord,
    ArtifactRepairMetadata,
    ArtifactStatus,
    ModeDefinition,
    ModeRegistry,
    ProcessContext,
    SessionMode,
    WorkflowState,
)
from metrology_process_planner.workflows import (
    ArtifactRepairStateMachine,
    MeasurementWorkflowStateMachine,
    RecipeContextStateMachine,
    SessionUIStateMachine,
)
from tests.editor_render_fixtures import session_without_pending

if __name__ == "__main__":
    unittest.main()


class UiStateMachineTestsPart2(unittest.TestCase):
    def test_loaded_recipe_free_registry_hides_recipe_context_for_process_named_mode(self) -> None:
        registry = ModeRegistry(
            (
                ModeDefinition(
                    SessionMode.PROFILOMETRY_PLANNER.value,
                    "Recipe Free Override",
                ),
            )
        )
        process_artifact = ArtifactRecord(
            "legacy-process-output",
            "process_output",
            "Legacy Process Output",
            "process_outputs/legacy-stack.png",
            ArtifactOwnerRef("capture", "cap-001", "stack_image"),
            status=ArtifactStatus.MISSING,
            repair=ArtifactRepairMetadata(
                repair_action="regenerate_process_output",
                requires_recipe=True,
                requires_solver=True,
            ),
        )
        current = replace(
            session_without_pending(),
            mode=SessionMode.PROFILOMETRY_PLANNER,
            process_context=ProcessContext(recipe_id="legacy-recipe", warning_ids=("warn-recipe",)),
            artifacts={process_artifact.id: process_artifact},
        )

        recipe = RecipeContextStateMachine(registry).evaluate(current)
        repair = ArtifactRepairStateMachine(registry).evaluate(current)

        self.assertEqual("hidden", recipe.state)
        self.assertEqual("idle", repair.state)
        self.assertNotIn("RegenerateProcessOutput", repair.action_ids)

    def test_recipe_and_artifact_repair_states_are_visible_for_process_sessions(self) -> None:
        current = session_without_pending()
        artifact_id, artifact = next(iter((current.artifacts or {}).items()))
        current = replace(
            current,
            mode=SessionMode.PROCESS_AWARE_METROLOGY,
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
        self.assertIn("RegenerateProcessOutput", repair.action_ids)

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
