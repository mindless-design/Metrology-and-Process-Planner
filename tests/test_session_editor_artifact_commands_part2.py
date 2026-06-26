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
    EditorActionDispatcher,
    EditorActionType,
    SessionDocumentBuilder,
)
from metrology_process_planner.workflows.editor.editing import select_item
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


class SessionEditorArtifactCommandTestsPart2(unittest.TestCase):
    def test_direct_relink_action_without_path_returns_precise_unavailable(self) -> None:
        crop = replace(artifact("crop"), status=ArtifactStatus.MISSING)
        document = select_item(
            SessionDocumentBuilder().build(session(artifacts={"crop": crop})),
            "capture:cap-001",
        )

        result = EditorActionDispatcher().dispatch(
            document,
            EditorAction(
                EditorActionType.RELINK_ARTIFACT,
                "Relink Artifact",
                "capture:cap-001",
                payload=(("artifact_id", "crop"),),
            ),
        )

        self.assertEqual("unavailable", result.status)
        self.assertEqual("Relink artifact requires a selected replacement path.", result.message)

    def test_direct_relink_action_updates_artifact_path(self) -> None:
        crop = replace(artifact("crop"), status=ArtifactStatus.MISSING)
        document = select_item(
            SessionDocumentBuilder().build(session(artifacts={"crop": crop})),
            "capture:cap-001",
        )

        result = EditorActionDispatcher().dispatch(
            document,
            EditorAction(
                EditorActionType.RELINK_ARTIFACT,
                "Relink Artifact",
                "capture:cap-001",
                payload=(("artifact_id", "crop"), ("relative_path", "images/new.png")),
            ),
        )

        self.assertEqual("success", result.status)
        self.assertEqual("images/new.png", result.document.session.artifacts["crop"].relative_path)

    def test_direct_relink_action_rejects_hidden_process_artifact_for_loaded_registry(
        self,
    ) -> None:
        registry = _recipe_free_registry_for(SessionMode.PROFILOMETRY_PLANNER.value)
        process_artifact = _process_artifact("process-output")
        source = replace(
            session(artifacts={process_artifact.id: process_artifact}),
            mode=SessionMode.PROFILOMETRY_PLANNER,
        )
        document = SessionDocumentBuilder(mode_registry=registry).build(source)

        result = EditorActionDispatcher(mode_registry=registry).dispatch(
            document,
            EditorAction(
                EditorActionType.RELINK_ARTIFACT,
                "Relink Artifact",
                "dashboard",
                payload=(
                    ("artifact_id", process_artifact.id),
                    ("relative_path", "images/new.png"),
                ),
            ),
        )

        self.assertEqual("unavailable", result.status)
        self.assertIn("recipe-free mode", result.message)
        self.assertEqual(
            process_artifact.relative_path,
            result.document.session.artifacts[process_artifact.id].relative_path,
        )

    def test_relink_with_payload_updates_artifact_path(self) -> None:
        services = build_app_services()
        crop = replace(artifact("crop"), status=ArtifactStatus.MISSING)
        document = select_item(
            SessionDocumentBuilder().build(session(artifacts={"crop": crop})),
            "capture:cap-001",
        )
        with TemporaryDirectory() as temp_dir:
            result = services.session_editor_controller.open_document(
                document,
                SessionPaths.for_folder(Path(temp_dir)),
            )
            relink = _action(result.window, EditorActionType.RELINK_ARTIFACT)
            relink = replace(
                relink,
                payload=relink.payload + (("relative_path", "images/new.png"),),
            )

            result.window["on_action"](relink)

        current = services.session_editor_controller.current_document
        self.assertIsNotNone(current)
        self.assertEqual("images/new.png", current.session.artifacts["crop"].relative_path)
