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
from metrology_process_planner.workflows.editor.view_models import EditorActionType
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

if __name__ == "__main__":
    unittest.main()


class ExternalModeEditorPolicyTestsPart4(unittest.TestCase):
    def test_registered_external_recipe_free_dashboard_uses_loaded_artifact_policy(self) -> None:
        registry = _external_metrology_registry(navigator_groups=("dashboard", "warnings"))
        visible = ArtifactRecord(
            "capture-missing",
            "capture_image",
            "Capture Missing",
            "captures/missing.png",
            ArtifactOwnerRef("capture", "cap-001", "site_image"),
            status=ArtifactStatus.MISSING,
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
        source = replace(
            session_without_pending(),
            mode=SessionModeId("external_mode"),
            artifacts={visible.id: visible, hidden_process.id: hidden_process},
        )
        document = SessionDocumentBuilder(mode_registry=registry).build(source)
        adapter = DefaultSessionModeAdapter(registry)

        fields = {
            field.key: field.value
            for field in adapter.metadata_fields(source, document.items_by_id["dashboard"])
        }
        actions = {
            action.action_type: action
            for action in adapter.actions(source, document.items_by_id["dashboard"])
        }

        self.assertEqual("1", fields["missing_artifact_count"])
        self.assertEqual("1", fields["artifact_attention_count"])
        self.assertEqual("missing required artifacts", fields["report_readiness"])
        self.assertTrue(actions[EditorActionType.REGENERATE_MISSING_ARTIFACTS].enabled)
