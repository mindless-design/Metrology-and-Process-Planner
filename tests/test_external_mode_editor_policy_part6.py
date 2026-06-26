import unittest
from dataclasses import replace

from metrology_process_planner.domains.session import (
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

if __name__ == "__main__":
    unittest.main()


class ExternalModeEditorPolicyTestsPart6(unittest.TestCase):
    def test_registered_external_recipe_free_capture_metadata_hides_process_fields(self) -> None:
        registry = _external_metrology_registry(navigator_groups=("dashboard", "captures"))
        source = replace(session_without_pending(), mode=SessionModeId("external_mode"))
        capture = replace(
            source.captures[0],
            extensions={
                "legacy_process": {
                    "process_context_ref": "process_context.active",
                    "solver_request": {"operation": "profile"},
                }
            },
        )
        source = replace(source, captures=(capture,))
        document = SessionDocumentBuilder(mode_registry=registry).build(source)
        adapter = DefaultSessionModeAdapter(registry)

        fields = adapter.metadata_fields(source, document.items_by_id["capture:cap-001"])

        self.assertNotIn("process_recipe", {field.key for field in fields})
        self.assertNotIn("solver_operation", {field.key for field in fields})
