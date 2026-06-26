import unittest
from dataclasses import replace

from metrology_process_planner.domains.session import (
    ArtifactOwnerRef,
    ArtifactRecord,
    ArtifactRepairMetadata,
    ArtifactStatus,
    EditorPolicy,
    MetadataFieldDefinition,
    MetadataSchema,
    ModeCapabilities,
    ModeDefinition,
    ModeRegistry,
    SessionModeId,
    SetupDefinition,
)
from metrology_process_planner.workflows.editor import (
    DefaultSessionModeAdapter,
    SessionDocumentBuilder,
)
from tests.editor_render_fixtures import session_without_pending


def _external_metrology_registry(
    *,
    uses_setup_guide: bool = False,
    supports_measurements: bool = False,
    include_capture_field: bool = False,
    navigator_groups: tuple[str, ...] | None = None,
    setup_stages: tuple[str, ...] = (),
) -> ModeRegistry:
    return ModeRegistry(
        (
            ModeDefinition(
                "external_mode",
                "External Mode",
                family="metrology",
                capabilities=ModeCapabilities(
                    uses_setup_guide=uses_setup_guide,
                    supports_grid_datasets=True,
                    supports_measurements=supports_measurements,
                ),
                setup=SetupDefinition(
                    required=bool(setup_stages),
                    can_skip=not bool(setup_stages),
                    stage_types=setup_stages,
                ),
                metadata=_metadata(include_capture_field),
                editor=EditorPolicy(
                    navigator_groups or ("dashboard", "setup", "captures", "warnings")
                ),
            ),
        )
    )

def _metadata(include_capture_field: bool) -> MetadataSchema:
    if not include_capture_field:
        return MetadataSchema()
    return MetadataSchema(
        capture_fields=(MetadataFieldDefinition("external_field", "External Field"),)
    )

class ExternalModeEditorPolicyTestsPart5(unittest.TestCase):
    def test_registered_external_recipe_free_capture_hides_process_artifact_refs(self) -> None:
        registry = _external_metrology_registry(navigator_groups=("dashboard", "captures"))
        source = _capture_with_hidden_process_artifact()
        document = SessionDocumentBuilder(mode_registry=registry).build(source)
        adapter = DefaultSessionModeAdapter(registry)
        capture = document.items_by_id["capture:cap-001"]

        actions = adapter.actions(source, capture)

        self.assertEqual({"capture-present"}, {ref.artifact_id for ref in capture.artifact_refs})
        self.assertEqual(
            ("capture-present",),
            tuple(
                detail.artifact_id
                for detail in document.artifact_details_by_item_id["capture:cap-001"]
            ),
        )
        self.assertEqual(0, document.artifact_health.missing)
        self.assertNotIn(
            "legacy-process-output",
            {
                value
                for action in actions
                for key, value in action.payload
                if key == "artifact_id"
            },
        )

    def test_registered_external_recipe_free_hides_process_owned_drawing_artifacts(self) -> None:
        registry = _external_metrology_registry(
            navigator_groups=("dashboard", "captures", "overviews")
        )
        hidden_process = ArtifactRecord(
            "legacy-cross-section",
            "CrossSectionImage",
            "Legacy Cross Section",
            "process_outputs/legacy-cross-section.png",
            ArtifactOwnerRef("legacy_drawing", "legacy-output", "cross_section_png"),
            status=ArtifactStatus.MISSING,
        )
        source = replace(
            session_without_pending(),
            mode=SessionModeId("external_mode"),
            artifacts={hidden_process.id: hidden_process},
        )

        document = SessionDocumentBuilder(mode_registry=registry).build(source)

        self.assertNotIn(
            "drawing:legacy_drawing:legacy-output:cross_section",
            document.items_by_id,
        )
        self.assertEqual(0, document.artifact_health.missing)


def _capture_with_hidden_process_artifact():
    visible = ArtifactRecord(
        "capture-present",
        "capture_image",
        "Capture Present",
        "captures/cap-001.png",
        ArtifactOwnerRef("capture", "cap-001", "site_image"),
        status=ArtifactStatus.PRESENT,
    )
    hidden_process = ArtifactRecord(
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
    return replace(
        session_without_pending(),
        mode=SessionModeId("external_mode"),
        artifacts={visible.id: visible, hidden_process.id: hidden_process},
    )
