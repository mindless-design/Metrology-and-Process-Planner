import unittest
from dataclasses import replace

from metrology_process_planner.domains.session import (
    EditorPolicy,
    GridDatasetRecord,
    MetadataFieldDefinition,
    MetadataSchema,
    ModeCapabilities,
    ModeDefinition,
    ModeRegistry,
    ReportRecord,
    SessionModeId,
    SetupDefinition,
    SetupState,
)
from metrology_process_planner.ui.session_editor import (
    InMemorySessionEditorWidgetFactory,
    SessionEditorCallbacks,
    SessionEditorShell,
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


class ExternalModeEditorPolicyTestsPart2(unittest.TestCase):
    def test_external_setup_mode_blocks_capture_until_required_stage(self) -> None:
        registry = _external_metrology_registry(
            uses_setup_guide=True,
            setup_stages=("required_optical_alignment_mark",),
        )
        source = replace(
            session_without_pending(),
            mode=SessionModeId("external_mode"),
            setup=SetupState(is_capture_ready=True),
        )
        document = SessionDocumentBuilder(mode_registry=registry).build(source)
        adapter = DefaultSessionModeAdapter(registry)

        window = SessionEditorShell(InMemorySessionEditorWidgetFactory()).open(
            document,
            adapter,
            SessionEditorCallbacks(lambda _item_id: None, lambda _action: None),
        )
        add_capture = next(
            action for action in window["primary_actions"] if action.label == "Add Capture"
        )

        self.assertFalse(add_capture.enabled)
        self.assertIn("Optical Alignment Mark", add_capture.disabled_reason)

    def test_registered_external_setup_mode_header_uses_loaded_setup_state(self) -> None:
        registry = _external_metrology_registry(
            uses_setup_guide=True,
            setup_stages=("required_optical_alignment_mark", "ready_for_capture"),
        )
        source = replace(
            session_without_pending(),
            mode=SessionModeId("external_mode"),
            setup=SetupState(is_capture_ready=True),
        )
        document = SessionDocumentBuilder(mode_registry=registry).build(source)
        adapter = DefaultSessionModeAdapter(registry)

        window = SessionEditorShell(InMemorySessionEditorWidgetFactory()).open(
            document,
            adapter,
            SessionEditorCallbacks(lambda _item_id: None, lambda _action: None),
        )

        header = dict(window["header"])
        add_capture = next(
            action for action in window["primary_actions"] if action.label == "Add Capture"
        )

        self.assertEqual("alignment_required", header["Setup"])
        self.assertFalse(add_capture.enabled)
        self.assertIn("Optical Alignment Mark", add_capture.disabled_reason)

    def test_registered_external_mode_filters_navigator_groups_from_policy(self) -> None:
        registry = _external_metrology_registry(
            navigator_groups=("dashboard", "captures", "warnings")
        )
        source = replace(
            session_without_pending(),
            mode=SessionModeId("external_mode"),
            grid_datasets=(GridDatasetRecord("grid-001", "Hidden Grid"),),
            reports=(ReportRecord("report-001", "Hidden Report", "summary"),),
        )

        document = SessionDocumentBuilder(mode_registry=registry).build(source)
        group_labels = [group.label for group in document.navigator_groups]

        self.assertIn("grid:grid-001", document.items_by_id)
        self.assertIn("report:report-001", document.items_by_id)
        self.assertEqual(["Dashboard", "Saved Captures"], group_labels)
