import unittest
from dataclasses import replace

from metrology_process_planner.domains.session import (
    ArtifactOwnerRef,
    ArtifactRecord,
    ArtifactRepairMetadata,
    ArtifactStatus,
    ModeDefinition,
    ModeRegistry,
    SessionMode,
)
from metrology_process_planner.workflows.editor import (
    DefaultSessionModeAdapter,
    SessionDocumentBuilder,
)
from tests.editor_render_fixtures import session_without_pending


def _recipe_free_registry_for(mode_id: str) -> ModeRegistry:
    return ModeRegistry((ModeDefinition(mode_id, "Recipe Free Override"),))

if __name__ == "__main__":
    unittest.main()


class NonProcessEditorLegacyArtifactTestsPart1(unittest.TestCase):
    def test_orphaned_process_output_artifact_does_not_create_cross_section_item(self) -> None:
        source = replace(
            session_without_pending(),
            artifacts={
                "legacy-process-svg": ArtifactRecord(
                    "legacy-process-svg",
                    "process_output",
                    "Legacy Process SVG",
                    "process_outputs/legacy.svg",
                    ArtifactOwnerRef("process_output", "legacy-output", "cross_section_svg"),
                    status=ArtifactStatus.MISSING,
                )
            },
        )

        document = SessionDocumentBuilder().build(source)

        self.assertNotIn("drawing:process_output:legacy-output:cross_section", document.items_by_id)
        self.assertNotIn("Cross Sections", {group.label for group in document.navigator_groups})
        self.assertEqual(0, document.artifact_health.missing)

    def test_capture_inspector_ignores_hidden_process_artifact_roles(self) -> None:
        source = session_without_pending()
        artifacts = dict(source.artifacts or {})
        artifacts["legacy-process-crop"] = ArtifactRecord(
            "legacy-process-crop",
            "process_output",
            "Legacy Process Crop",
            "process_outputs/cap-001-crop.png",
            ArtifactOwnerRef("capture", "cap-001", "crop"),
            status=ArtifactStatus.MISSING,
        )
        document = SessionDocumentBuilder().build(replace(source, artifacts=artifacts))
        capture = document.items_by_id["capture:cap-001"]

        fields = DefaultSessionModeAdapter().metadata_fields(document.session, capture)

        values = {field.key: field.value for field in fields}
        self.assertEqual("present", values["site_image_status"])

    def test_loaded_recipe_free_capture_inspector_hides_process_artifacts_for_process_named_mode(
        self,
    ) -> None:
        source = replace(session_without_pending(), mode=SessionMode.PROFILOMETRY_PLANNER)
        visible = next(iter(source.artifacts.values()))
        hidden = ArtifactRecord(
            "legacy-site-image-process-output",
            "process_output",
            "Legacy Process Site Image",
            "process_outputs/cap-001-site.png",
            ArtifactOwnerRef("capture", "cap-001", "site_image"),
            status=ArtifactStatus.MISSING,
            repair=ArtifactRepairMetadata(
                repair_action="regenerate_process_output",
                requires_recipe=True,
                requires_solver=True,
            ),
        )
        registry = _recipe_free_registry_for(source.mode.value)
        document = SessionDocumentBuilder(mode_registry=registry).build(
            replace(source, artifacts={hidden.id: hidden, visible.id: visible})
        )
        capture = document.items_by_id["capture:cap-001"]

        fields = DefaultSessionModeAdapter(registry).metadata_fields(document.session, capture)

        values = {field.key: field.value for field in fields}
        self.assertEqual("present", values["site_image_status"])

    def test_capture_owned_process_artifact_is_hidden_from_recipe_free_editor(self) -> None:
        source = session_without_pending()
        artifacts = dict(source.artifacts or {})
        artifacts["legacy-capture-process-output"] = ArtifactRecord(
            "legacy-capture-process-output",
            "process_output",
            "Legacy Capture Process Output",
            "process_outputs/cap-001-stack.png",
            ArtifactOwnerRef("capture", "cap-001", "stack_image"),
            status=ArtifactStatus.MISSING,
        )

        document = SessionDocumentBuilder().build(replace(source, artifacts=artifacts))
        capture_item = document.items_by_id["capture:cap-001"]

        self.assertNotIn(
            "legacy-capture-process-output",
            {artifact.artifact_id for artifact in capture_item.artifact_refs},
        )
        self.assertNotIn(
            "legacy-capture-process-output",
            {
                artifact.artifact_id
                for artifact in document.artifact_details_by_item_id["capture:cap-001"]
            },
        )
        self.assertEqual(0, document.artifact_health.missing)
