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
    SessionDocumentBuilder,
)
from tests.editor_render_fixtures import session_without_pending


def _recipe_free_registry_for(mode_id: str) -> ModeRegistry:
    return ModeRegistry((ModeDefinition(mode_id, "Recipe Free Override"),))

if __name__ == "__main__":
    unittest.main()


class NonProcessEditorLegacyArtifactTestsPart2(unittest.TestCase):
    def test_generic_orphaned_process_drawing_role_is_hidden_from_recipe_free_editor(self) -> None:
        source = session_without_pending()
        artifacts = dict(source.artifacts or {})
        artifacts["legacy-cross-section-svg"] = ArtifactRecord(
            "legacy-cross-section-svg",
            "svg",
            "Legacy Cross Section SVG",
            "process_outputs/legacy-cross-section.svg",
            ArtifactOwnerRef("legacy_drawing", "legacy-output", "cross_section_svg"),
            status=ArtifactStatus.MISSING,
        )

        document = SessionDocumentBuilder().build(replace(source, artifacts=artifacts))

        self.assertNotIn(
            "drawing:legacy_drawing:legacy-output:cross_section",
            document.items_by_id,
        )
        self.assertNotIn("Cross Sections", {group.label for group in document.navigator_groups})
        self.assertEqual(0, document.artifact_health.missing)

    def test_external_process_artifact_name_variants_are_hidden_from_recipe_free_editor(
        self,
    ) -> None:
        source = session_without_pending()
        artifacts = dict(source.artifacts or {})
        artifacts["legacy-stack-image-png"] = ArtifactRecord(
            "legacy-stack-image-png",
            "Stack Image PNG",
            "Legacy Stack Image",
            "process_outputs/legacy-stack.png",
            ArtifactOwnerRef("capture", "cap-001", "Stack Image PNG"),
            status=ArtifactStatus.MISSING,
        )
        artifacts["legacy-cross-section-image"] = ArtifactRecord(
            "legacy-cross-section-image",
            "CrossSectionImage",
            "Legacy Cross Section Image",
            "process_outputs/legacy-cross-section.png",
            ArtifactOwnerRef("legacy_drawing", "legacy-output", "legacyCrossSection"),
            status=ArtifactStatus.MISSING,
        )

        document = SessionDocumentBuilder().build(replace(source, artifacts=artifacts))
        capture_item = document.items_by_id["capture:cap-001"]

        self.assertNotIn(
            "legacy-stack-image-png",
            {artifact.artifact_id for artifact in capture_item.artifact_refs},
        )
        self.assertNotIn(
            "drawing:legacy_drawing:legacy-output:cross_section",
            document.items_by_id,
        )
        self.assertEqual(0, document.artifact_health.missing)

    def test_loaded_recipe_free_override_hides_process_overview_roles_for_process_named_mode(
        self,
    ) -> None:
        source = replace(session_without_pending(), mode=SessionMode.PROFILOMETRY_PLANNER)
        hidden = ArtifactRecord(
            "legacy-stack-overview",
            "overview_image",
            "Legacy Stack Overview",
            "process_outputs/stack-overview.svg",
            ArtifactOwnerRef("session", source.id, "stack_image"),
            status=ArtifactStatus.MISSING,
            repair=ArtifactRepairMetadata(
                repair_action="regenerate_process_output",
                requires_recipe=True,
                requires_solver=True,
            ),
        )
        registry = _recipe_free_registry_for(source.mode.value)

        document = SessionDocumentBuilder(mode_registry=registry).build(
            replace(source, artifacts={hidden.id: hidden})
        )

        self.assertNotIn("overview:stack_image", document.items_by_id)
        self.assertEqual(0, document.artifact_health.missing)
