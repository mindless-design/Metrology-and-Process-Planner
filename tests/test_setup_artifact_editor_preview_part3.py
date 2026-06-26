import unittest
from dataclasses import replace
from pathlib import Path
from tempfile import TemporaryDirectory

from metrology_process_planner.domains.modes.mode_policies import ModeCapabilities
from metrology_process_planner.domains.session import (
    ArtifactOwnerRef,
    ArtifactRecord,
    ArtifactRepairMetadata,
    ArtifactStatus,
    ModeDefinition,
    ModeRegistry,
    SessionMode,
    SetupItemRecord,
    SetupState,
)
from metrology_process_planner.persistence.paths import SessionPaths
from metrology_process_planner.workflows.editor import EditorAction, EditorActionDispatcher
from metrology_process_planner.workflows.editor.adapters import DefaultSessionModeAdapter
from metrology_process_planner.workflows.editor.builder import SessionDocumentBuilder
from metrology_process_planner.workflows.editor.view_models import EditorActionType
from tests.editor_render_fixtures import empty_session


def _complete_setup_item(item_id: str) -> SetupItemRecord:
    return SetupItemRecord(
        item_id,
        "alignment_box_capture",
        "Optical Alignment Mark",
        "complete",
        metadata={"required": True},
    )

def _missing_setup_artifact() -> ArtifactRecord:
    return ArtifactRecord(
        "setup-optical-alignment",
        "setup_reference_image",
        "Optical Alignment",
        "images/setup-optical_alignment.png",
        ArtifactOwnerRef("setup", "optical_alignment", "optical_alignment_image"),
        status=ArtifactStatus.MISSING,
        repair=ArtifactRepairMetadata(
            repair_action="regenerate_artifact",
            repair_suggestion="Regenerate the setup image.",
            regenerable=True,
        ),
    )

def _session_with_setup_artifact(artifact: ArtifactRecord):
    return replace(
        empty_session(),
        mode=SessionMode.OPTICAL_METROLOGY,
        artifacts={artifact.id: artifact},
        setup=SetupState(
            items=(
                SetupItemRecord(
                    "optical_alignment",
                    "alignment_box_capture",
                    "Optical Alignment Mark",
                    "complete",
                    artifact_refs={"optical_alignment_image": artifact.id},
                ),
            )
        ),
    )

def _recipe_free_setup_registry_for(mode_id: str) -> ModeRegistry:
    return ModeRegistry(
        (
            ModeDefinition(
                mode_id,
                "Recipe Free Setup Override",
                capabilities=ModeCapabilities(uses_setup_guide=True),
            ),
        )
    )

if __name__ == "__main__":
    unittest.main()


class SetupArtifactEditorPreviewTestsPart3(unittest.TestCase):
    def test_setup_item_exposes_artifact_repair_actions(self) -> None:
        artifact = _missing_setup_artifact()
        source = _session_with_setup_artifact(artifact)
        document = SessionDocumentBuilder().build(source)
        setup = document.items_by_id["setup"]

        actions = DefaultSessionModeAdapter().actions(source, setup)
        repair = next(
            action for action in actions
            if action.action_type is EditorActionType.REGENERATE_ARTIFACT
        )
        relink = next(
            action for action in actions
            if action.action_type is EditorActionType.RELINK_ARTIFACT
        )

        self.assertEqual((("artifact_id", artifact.id),), repair.payload)
        self.assertEqual((("artifact_id", artifact.id),), relink.payload)

    def test_setup_artifact_regenerate_routes_through_repair_service(self) -> None:
        artifact = _missing_setup_artifact()
        source = _session_with_setup_artifact(artifact)
        document = SessionDocumentBuilder().build(source)

        with TemporaryDirectory() as temp_dir:
            result = EditorActionDispatcher(
                paths=SessionPaths.for_folder(Path(temp_dir)),
            ).dispatch(
                document,
                EditorAction(
                    EditorActionType.REGENERATE_ARTIFACT,
                    "Regenerate Setup Artifact",
                    "setup",
                    payload=(("artifact_id", artifact.id),),
                ),
            )

        repaired = result.document.session.artifacts[artifact.id]

        self.assertEqual("success", result.status)
        self.assertEqual("Regenerated setup artifact.", result.message)
        self.assertEqual(ArtifactStatus.MISSING, repaired.status)
        self.assertTrue(repaired.warning_ids)
        self.assertIn(
            "GENERATOR_HANDLER_UNAVAILABLE",
            {warning.code for warning in result.document.session.warnings},
        )
