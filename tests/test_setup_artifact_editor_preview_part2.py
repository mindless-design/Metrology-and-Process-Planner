import unittest
from dataclasses import replace

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


class SetupArtifactEditorPreviewTestsPart2(unittest.TestCase):
    def test_loaded_recipe_free_setup_hides_process_artifacts_for_process_named_mode(
        self,
    ) -> None:
        artifact = ArtifactRecord(
            "legacy-process-output",
            "process_output",
            "Legacy Process Output",
            "process_outputs/legacy.json",
            ArtifactOwnerRef("setup", "reference", "stack_image"),
            status=ArtifactStatus.MISSING,
            repair=ArtifactRepairMetadata(
                repair_action="regenerate_process_output",
                requires_recipe=True,
                requires_solver=True,
            ),
        )
        registry = _recipe_free_setup_registry_for(SessionMode.PROFILOMETRY_PLANNER.value)
        source = replace(
            empty_session(),
            mode=SessionMode.PROFILOMETRY_PLANNER,
            artifacts={artifact.id: artifact},
            setup=SetupState(
                items=(
                    SetupItemRecord(
                        "reference",
                        "origin_reference_box_capture",
                        "Reference Image",
                        "complete",
                        artifact_refs={"stack": artifact.id},
                    ),
                )
            ),
        )

        document = SessionDocumentBuilder(mode_registry=registry).build(source)
        setup = document.items_by_id["setup"]
        adapter = DefaultSessionModeAdapter(registry)
        fields = {
            field.key: field.value
            for field in adapter.metadata_fields(source, setup)
        }
        previews = adapter.preview_options(source, setup)

        self.assertEqual((), setup.artifact_refs)
        self.assertEqual("0", fields["setup_artifacts"])
        self.assertEqual("No preview available.", previews[0].placeholder)

    def test_setup_item_uses_setup_metadata_and_actions(self) -> None:
        source = replace(
            empty_session(),
            mode=SessionMode.CDSEM_MEASUREMENT,
            setup=SetupState(items=(_complete_setup_item("optical_alignment"),)),
        )
        document = SessionDocumentBuilder().build(source)
        setup = document.items_by_id["setup"]
        adapter = DefaultSessionModeAdapter()

        fields = {
            field.key: field.value
            for field in adapter.metadata_fields(source, setup)
        }
        actions = adapter.actions(source, setup)
        action_types = {action.action_type for action in actions}

        self.assertEqual("cdsem_measurement", fields["mode"])
        self.assertEqual("incomplete", fields["setup_status"])
        self.assertEqual("Origin Reference Image", fields["current_stage"])
        self.assertEqual("2", fields["completed_stages"])
        self.assertEqual("SEM Alignment Mark", fields["required_incomplete"])
        self.assertIn(EditorActionType.REOPEN_SETUP, action_types)
        self.assertNotIn(EditorActionType.GENERATE_SESSION_OVERVIEW, action_types)
        self.assertNotIn(EditorActionType.SCAN_ARTIFACTS, action_types)
