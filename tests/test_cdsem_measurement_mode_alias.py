import unittest
from dataclasses import replace

from metrology_process_planner.domains.session import SessionMode, built_in_mode_registry
from metrology_process_planner.workflows.mode_capture_defaults import capture_defaults
from tests.editor_render_fixtures import session


class CdsemMeasurementModeAliasTests(unittest.TestCase):
    def test_cdsem_measurement_is_registered_as_recipe_free_mode(self) -> None:
        definition = built_in_mode_registry().definition(SessionMode.CDSEM_MEASUREMENT.value)

        self.assertEqual("cdsem_measurement", definition.mode_id)
        self.assertEqual("forbidden", definition.process.recipe_policy)
        self.assertEqual("none", definition.process.solver_operation)
        self.assertFalse(definition.capabilities.supports_process_solver)
        self.assertFalse(definition.editor.process_context_visible)
        self.assertIn("required_sem_alignment_mark", definition.setup.stage_types)

    def test_legacy_cdsem_capture_mode_remains_registered(self) -> None:
        registry = built_in_mode_registry()

        self.assertIn(SessionMode.CDSEM_CAPTURE.value, registry.mode_ids())
        self.assertIn(SessionMode.CDSEM_MEASUREMENT.value, registry.mode_ids())

    def test_cdsem_planning_alias_is_registered_but_hidden(self) -> None:
        registry = built_in_mode_registry()
        definition = registry.definition(SessionMode.CDSEM_PLANNING.value)

        self.assertIn(SessionMode.CDSEM_PLANNING.value, registry.mode_ids())
        self.assertNotIn(SessionMode.CDSEM_PLANNING.value, registry.visible_mode_ids())
        self.assertEqual("forbidden", definition.process.recipe_policy)
        self.assertEqual("none", definition.process.solver_operation)
        self.assertFalse(definition.capabilities.supports_process_solver)
        self.assertFalse(definition.editor.process_context_visible)
        self.assertIn("required_sem_alignment_mark", definition.setup.stage_types)

    def test_cdsem_measurement_defaults_match_cdsem_site_capture(self) -> None:
        current = session()
        pending = current.pending_captures[0]
        current = replace(current, mode=SessionMode.CDSEM_MEASUREMENT)

        metadata = capture_defaults(current, pending, "cap-001", "")

        self.assertEqual("cdsem_site", metadata.role)
        self.assertEqual("cdsem_site", metadata.capture_type)

    def test_cdsem_planning_defaults_match_cdsem_site_capture(self) -> None:
        current = session()
        pending = current.pending_captures[0]
        current = replace(current, mode=SessionMode.CDSEM_PLANNING)

        metadata = capture_defaults(current, pending, "cap-001", "")

        self.assertEqual("cdsem_site", metadata.role)
        self.assertEqual("cdsem_site", metadata.capture_type)

if __name__ == "__main__":
    unittest.main()
