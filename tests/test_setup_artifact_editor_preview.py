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


class SetupArtifactEditorPreviewTestsPart1(unittest.TestCase):
    def test_setup_item_exposes_visible_setup_artifacts_for_preview(self) -> None:
        artifact = ArtifactRecord(
            "setup-optical-alignment",
            "setup_reference_image",
            "Optical Alignment",
            "images/setup-optical_alignment.png",
            ArtifactOwnerRef("setup", "optical_alignment", "optical_alignment_image"),
            status=ArtifactStatus.PRESENT,
        )
        source = replace(
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
                        artifact_refs={
                            "image": artifact.id,
                            "optical_alignment_image": artifact.id,
                        },
                    ),
                )
            ),
        )

        document = SessionDocumentBuilder().build(source)
        setup = document.items_by_id["setup"]
        fields = {
            field.key: field.value
            for field in DefaultSessionModeAdapter().metadata_fields(source, setup)
        }
        previews = DefaultSessionModeAdapter().preview_options(source, setup)

        self.assertEqual((artifact.id,), tuple(ref.artifact_id for ref in setup.artifact_refs))
        self.assertEqual("1", fields["setup_artifacts"])
        self.assertEqual("Optical Alignment Image", previews[0].label)
        self.assertEqual("images/setup-optical_alignment.png", previews[0].artifact_path)
        self.assertEqual("", previews[0].placeholder)

    def test_setup_item_hides_process_only_artifacts_for_recipe_free_modes(self) -> None:
        artifact = ArtifactRecord(
            "legacy-process-output",
            "process_output",
            "Legacy Process Output",
            "process_outputs/legacy.json",
            ArtifactOwnerRef("setup", "reference", "stack_image"),
            status=ArtifactStatus.MISSING,
        )
        source = replace(
            empty_session(),
            mode=SessionMode.OPTICAL_METROLOGY,
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

        document = SessionDocumentBuilder().build(source)
        setup = document.items_by_id["setup"]
        previews = DefaultSessionModeAdapter().preview_options(source, setup)

        self.assertEqual((), setup.artifact_refs)
        self.assertEqual("No preview available.", previews[0].placeholder)
