import unittest
from dataclasses import replace
from pathlib import Path
from tempfile import TemporaryDirectory

from metrology_process_planner.app.bootstrap import build_app_services
from metrology_process_planner.app.commands import CommandId
from metrology_process_planner.app.layout_crop_repair import layout_crop_repair_service
from metrology_process_planner.domains.session import (
    ArtifactRepairMetadata,
    ArtifactStatus,
    ModeDefinition,
    ModeRegistry,
    SourceLayoutContext,
)
from metrology_process_planner.persistence.paths import SessionPaths
from metrology_process_planner.workflows.editor import (
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


class SessionEditorArtifactCommandTestsPart1(unittest.TestCase):
    def test_injected_layout_crop_repair_service_repairs_selected_crop(self) -> None:
        services = build_app_services(
            artifact_repair_service=layout_crop_repair_service(_FakeCropExporter())
        )
        crop = replace(
            artifact("crop"),
            status=ArtifactStatus.MISSING,
            generator="layout_crop",
        )
        document = select_item(
            SessionDocumentBuilder().build(
                replace(
                    session(artifacts={"crop": crop}),
                    source_layout=SourceLayoutContext(layout_path="source.gds"),
                )
            ),
            "capture:cap-001",
        )
        with TemporaryDirectory() as temp_dir:
            result = services.session_editor_controller.open_document(
                document,
                SessionPaths.for_folder(Path(temp_dir)),
            )

            action = _action(result.window, EditorActionType.REGENERATE_ARTIFACT)
            result.window["on_action"](action)

        current = services.session_editor_controller.current_document
        self.assertIsNotNone(current)
        self.assertEqual(ArtifactStatus.PRESENT, current.session.artifacts["crop"].status)

    def test_selected_artifact_regeneration_routes_through_repair_service(self) -> None:
        services = build_app_services()
        crop = replace(artifact("crop"), status=ArtifactStatus.MISSING)
        document = select_item(
            SessionDocumentBuilder().build(
                replace(
                    session(artifacts={"crop": crop}),
                    source_layout=SourceLayoutContext(layout_path="source.gds"),
                )
            ),
            "capture:cap-001",
        )
        with TemporaryDirectory() as temp_dir:
            result = services.session_editor_controller.open_document(
                document,
                SessionPaths.for_folder(Path(temp_dir)),
            )

            action = _action(result.window, EditorActionType.REGENERATE_ARTIFACT)
            result.window["on_action"](action)

        current = services.session_editor_controller.current_document
        self.assertIsNotNone(current)
        self.assertIn("GENERATOR_HANDLER_UNAVAILABLE", {w.code for w in current.session.warnings})

    def test_bulk_missing_repair_scans_before_processing_queue(self) -> None:
        services = build_app_services()
        crop = replace(artifact("crop"), status=ArtifactStatus.PRESENT)
        document = SessionDocumentBuilder().build(session(artifacts={"crop": crop}))
        with TemporaryDirectory() as temp_dir:
            services.session_editor_controller.open_document(
                document,
                SessionPaths.for_folder(Path(temp_dir)),
            )

            routed = services.command_router.route(CommandId.REGENERATE_MISSING_ARTIFACTS)

        current = services.session_editor_controller.current_document
        self.assertEqual("success", routed.status)
        self.assertIsNotNone(current)
        self.assertEqual(ArtifactStatus.MISSING, current.session.artifacts["crop"].status)

    def test_relink_without_path_payload_returns_unavailable(self) -> None:
        services = build_app_services()

        routed = services.command_router.route(CommandId.RELINK_ARTIFACT)

        self.assertEqual("unavailable", routed.status)
        self.assertIn("replacement path", routed.message)
