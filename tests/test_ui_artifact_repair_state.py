import unittest
from dataclasses import replace

from metrology_process_planner.domains.session import (
    ArtifactRepairMetadata,
    ArtifactStatus,
    SessionMode,
)
from metrology_process_planner.workflows import ArtifactRepairStateMachine
from tests.editor_render_fixtures import session_without_pending


class UiArtifactRepairStateTests(unittest.TestCase):
    def test_process_repair_action_is_hidden_for_non_process_artifact_tasks(self) -> None:
        current = session_without_pending()
        artifact_id, artifact = next(iter((current.artifacts or {}).items()))
        current = replace(
            current,
            artifacts={
                artifact_id: replace(
                    artifact,
                    status=ArtifactStatus.MISSING,
                    warning_ids=("warn-artifact",),
                )
            },
        )

        snapshot = ArtifactRepairStateMachine().evaluate(current)

        self.assertEqual("open_tasks", snapshot.state)
        self.assertEqual(("RegenerateArtifact",), snapshot.action_ids)

    def test_process_repair_action_remains_available_for_process_modes(self) -> None:
        current = replace(session_without_pending(), mode=SessionMode.PROCESS_AWARE_METROLOGY)
        artifact_id, artifact = next(iter((current.artifacts or {}).items()))
        current = replace(
            current,
            artifacts={artifact_id: replace(artifact, status=ArtifactStatus.MISSING)},
        )

        snapshot = ArtifactRepairStateMachine().evaluate(current)

        self.assertIn("RegenerateArtifact", snapshot.action_ids)
        self.assertIn("RegenerateProcessOutput", snapshot.action_ids)

    def test_placeholder_repair_metadata_creates_artifact_repair_task(self) -> None:
        current = session_without_pending()
        artifact_id, artifact = next(iter((current.artifacts or {}).items()))
        current = replace(
            current,
            artifacts={
                artifact_id: replace(
                    artifact,
                    status=ArtifactStatus.PLACEHOLDER,
                    repair=ArtifactRepairMetadata(repair_action="generate_grid_overview"),
                )
            },
        )

        snapshot = ArtifactRepairStateMachine().evaluate(current)

        self.assertEqual("open_tasks", snapshot.state)
        self.assertEqual(("RegenerateArtifact",), snapshot.action_ids)

    def test_process_only_repair_artifact_is_hidden_for_non_process_modes(self) -> None:
        current = session_without_pending()
        artifact_id, artifact = next(iter((current.artifacts or {}).items()))
        current = replace(
            current,
            artifacts={
                artifact_id: replace(
                    artifact,
                    type="process_output",
                    status=ArtifactStatus.MISSING,
                    repair=ArtifactRepairMetadata(
                        repair_action="regenerate_process_output",
                        regenerable=True,
                        requires_recipe=True,
                    ),
                )
            },
        )

        snapshot = ArtifactRepairStateMachine().evaluate(current)

        self.assertEqual("idle", snapshot.state)
        self.assertEqual((), snapshot.action_ids)


if __name__ == "__main__":
    unittest.main()
