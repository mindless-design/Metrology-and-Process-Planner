import json
import tempfile
import unittest
from pathlib import Path

from metrology_process_planner.app.diagnostics import AdvancedDiagnosticsController
from metrology_process_planner.diagnostics import (
    DiagnosticsService,
    InMemoryDiagnosticSink,
)
from metrology_process_planner.domains.session import (
    CaptureSequenceDefinition,
    ModeDefinition,
    ModeRegistry,
    ModeWorkflowPlanner,
    SessionMode,
    built_in_mode_registry,
    load_mode_registry_from_folder,
)
from tests.editor_render_fixtures import session_without_pending


class ModeRegistryTests(unittest.TestCase):
    def test_builtin_modes_are_registered_and_valid(self) -> None:
        registry = built_in_mode_registry()

        self.assertEqual({mode.value for mode in SessionMode}, set(registry.mode_ids()))
        self.assertEqual((), registry.validation_warnings())
        self.assertTrue(registry.definition("simple_capture").capabilities.supports_measurements)
        self.assertIn(
            "site_box",
            registry.definition("process_aware_metrology").capture.supported_primitives,
        )

    def test_visible_mode_catalog_hides_legacy_and_internal_modes(self) -> None:
        registry = built_in_mode_registry()

        visible_ids = set(registry.visible_mode_ids())

        self.assertIn(SessionMode.CDSEM_MEASUREMENT.value, visible_ids)
        self.assertIn(SessionMode.PROFILOMETRY_PLANNER.value, visible_ids)
        self.assertNotIn(SessionMode.SIMPLE_LABELED_CAPTURE.value, visible_ids)
        self.assertNotIn(SessionMode.CAD_REVIEW_CAPTURE.value, visible_ids)
        self.assertNotIn(SessionMode.CDSEM_CAPTURE.value, visible_ids)
        self.assertNotIn(SessionMode.CDSEM_PLANNING.value, visible_ids)
        self.assertNotIn(SessionMode.PROCESS_AWARE_METROLOGY.value, visible_ids)
        self.assertNotIn(SessionMode.PROCESS_FLOW_SUMMARY.value, visible_ids)
        self.assertFalse(registry.definition(SessionMode.CDSEM_CAPTURE.value).visible)
        self.assertFalse(registry.definition(SessionMode.CDSEM_PLANNING.value).visible)

    def test_process_flow_summary_is_hidden_report_only_compatibility_mode(self) -> None:
        definition = built_in_mode_registry().definition(SessionMode.PROCESS_FLOW_SUMMARY.value)

        self.assertFalse(definition.visible)
        self.assertEqual("process_flow", definition.family)
        self.assertEqual("report_only_compatibility", definition.extensions["mode_scope"])
        self.assertTrue(definition.capabilities.supports_reporting)
        self.assertFalse(definition.capabilities.supports_process_solver)
        self.assertFalse(definition.capabilities.uses_canvas_objects)
        self.assertEqual("forbidden", definition.process.recipe_policy)
        self.assertEqual("none", definition.process.solver_operation)
        self.assertFalse(definition.editor.process_context_visible)
        self.assertEqual(("process_flow_summary",), definition.reporting.sections)


class ExternalModeDefinitionLoadTests(unittest.TestCase):
    """External and custom mode registry behavior."""

    def test_invalid_custom_mode_reports_warnings_without_raising(self) -> None:
        registry = ModeRegistry(
            (
                ModeDefinition("", "", capture=CaptureSequenceDefinition(supported_primitives=())),
                ModeDefinition("simple_capture", "Duplicate"),
                ModeDefinition(
                    "simple_capture",
                    "Duplicate 2",
                    capture=CaptureSequenceDefinition(supported_primitives=("point_capture",)),
                ),
            )
        )

        warnings = registry.validation_warnings()

        self.assertTrue(any("Mode id is required." in warning for warning in warnings))
        self.assertTrue(any("Mode label is required." in warning for warning in warnings))
        self.assertTrue(any("At least one capture primitive" in warning for warning in warnings))
        self.assertTrue(any("Duplicate mode id: simple_capture" in warning for warning in warnings))

    def test_workflow_planner_generates_compound_request_from_mode_policy(self) -> None:
        definition = built_in_mode_registry().definition("profilometry_planner")

        request = ModeWorkflowPlanner().compound_capture_request(definition)

        self.assertEqual("site_then_line", request.sequence_type)
        self.assertEqual("profilometry_site", request.site_role)
        self.assertEqual("profilometry_line", request.child_role)
        self.assertEqual("line_profile", request.solver_operation)

    def test_process_aware_modes_declare_editor_setup_and_reporting_policy(self) -> None:
        registry = built_in_mode_registry()
        profilometry = registry.definition("profilometry_planner")
        ellipsometry = registry.definition("ellipsometry_planner")

        self.assertEqual("recommended", profilometry.setup.origin_policy)
        self.assertIn("recipe_context", profilometry.setup.stage_types)
        self.assertIn("line_annotation", profilometry.editor.preview_modes)
        self.assertIn("point_annotation", ellipsometry.editor.preview_modes)
        self.assertIn("regenerate_process_output", profilometry.editor.actions)
        self.assertTrue(profilometry.reporting.enabled)
        self.assertIn("cross_section", profilometry.reporting.sections)
        self.assertIn("film_thickness_summary", ellipsometry.reporting.sections)

    def test_diagnostics_can_show_loaded_external_mode_registry(self) -> None:
        registry = ModeRegistry(
            built_in_mode_registry().definitions()
            + (ModeDefinition("profilometry_site_line", "Profilometry Site Line"),)
        )
        sink = InMemoryDiagnosticSink()
        controller = AdvancedDiagnosticsController(
            sink,
            DiagnosticsService(sink),
            mode_registry=registry,
        )
        controller.set_active_session(session_without_pending())

        result = controller.open_current()

        self.assertIn("profilometry_site_line", dict(result.window["summary"])["Loaded Modes"])


class ExternalModeRegistryTests(unittest.TestCase):
    def test_loads_external_mode_definitions_from_json_folder(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            folder = Path(temp_dir)
            (folder / "profilometry.json").write_text(
                json.dumps(
                    {
                        "mode_id": "profilometry_site_line",
                        "label": "Profilometry Site Line",
                        "primitives": ["site_box", "measurement"],
                        "supports_measurements": True,
                        "editor_groups": ["dashboard", "captures", "measurements"],
                        "adapter_id": "default",
                        "python": "this field is inert data and must not execute",
                    }
                ),
                encoding="utf-8",
            )

            result = load_mode_registry_from_folder(folder)

        definition = result.registry.definition("profilometry_site_line")
        self.assertEqual((), result.warnings)
        self.assertEqual("Profilometry Site Line", definition.display_name)
        self.assertEqual(("site_box", "measurement"), definition.capture.supported_primitives)
        self.assertTrue(definition.capabilities.supports_measurements)

    def test_invalid_external_mode_files_return_warnings(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            folder = Path(temp_dir)
            (folder / "broken.json").write_text("{not json", encoding="utf-8")
            (folder / "invalid.json").write_text(
                json.dumps({"modes": [{"mode_id": "", "label": "", "primitives": []}, 42]}),
                encoding="utf-8",
            )

            result = load_mode_registry_from_folder(folder)

        self.assertTrue(any("Invalid JSON" in warning for warning in result.warnings))
        self.assertTrue(
            any("Mode entry 2 is not an object" in warning for warning in result.warnings)
        )
        self.assertTrue(any("Mode id is required." in warning for warning in result.warnings))


if __name__ == "__main__":
    unittest.main()
