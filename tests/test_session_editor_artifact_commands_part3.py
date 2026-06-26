import unittest
from dataclasses import replace
from pathlib import Path
from tempfile import TemporaryDirectory

from metrology_process_planner.app.bootstrap import build_app_services
from metrology_process_planner.domains.session import (
    ArtifactRepairMetadata,
    ArtifactStatus,
    ModeDefinition,
    ModeRegistry,
    SessionMode,
)
from metrology_process_planner.persistence.paths import SessionPaths
from metrology_process_planner.workflows.editor import (
    EditorAction,
    EditorActionType,
    SessionDocumentBuilder,
)
from tests.artifact_lifecycle_fixtures import artifact, session


def _action(window, action_type: EditorActionType):
    return next(action for action in window["actions"] if action.action_type is action_type)

class _FakeCropExporter:
    def export_image(self, _bounds, destination):
        destination.write_text("crop", encoding="utf-8")
        return None

def _process_artifact(artifact_id: str):
    return replace(
        artifact(artifact_id, "process_outputs/legacy.json"),
        type="process_output",
        status=ArtifactStatus.MISSING,
        repair=ArtifactRepairMetadata(
            repair_action="regenerate_process_output",
            regenerable=True,
            requires_recipe=True,
            requires_solver=True,
        ),
    )

def _recipe_free_registry_for(mode_id: str) -> ModeRegistry:
    return ModeRegistry((ModeDefinition(mode_id, "Recipe Free Override"),))

if __name__ == "__main__":
    unittest.main()


class SessionEditorArtifactCommandTestsPart3(unittest.TestCase):
    def test_app_relink_command_rejects_hidden_process_artifact_for_loaded_registry(
        self,
    ) -> None:
        registry = _recipe_free_registry_for(SessionMode.PROFILOMETRY_PLANNER.value)
        services = build_app_services(mode_registry=registry)
        process_artifact = _process_artifact("process-output")
        source = replace(
            session(artifacts={process_artifact.id: process_artifact}),
            mode=SessionMode.PROFILOMETRY_PLANNER,
        )
        document = SessionDocumentBuilder(mode_registry=registry).build(source)
        with TemporaryDirectory() as temp_dir:
            result = services.session_editor_controller.open_document(
                document,
                SessionPaths.for_folder(Path(temp_dir)),
            )

            result.window["on_action"](
                EditorAction(
                    EditorActionType.RELINK_ARTIFACT,
                    "Relink Artifact",
                    "dashboard",
                    payload=(
                        ("artifact_id", process_artifact.id),
                        ("relative_path", "images/new.png"),
                    ),
                )
            )

        current = services.session_editor_controller.current_document
        routed = services.session_editor_controller.last_command_result
        self.assertIsNotNone(current)
        self.assertIsNotNone(routed)
        self.assertEqual("unavailable", routed.status)
        self.assertIn("recipe-free mode", routed.message)
        self.assertEqual(
            process_artifact.relative_path,
            current.session.artifacts[process_artifact.id].relative_path,
        )
