import unittest

from metrology_process_planner.domains.modes.mode_output_policies import (
    ArtifactOutputDefinition,
    ArtifactPolicy,
    EditorPolicy,
    ProcessPolicy,
    ReportingPolicy,
)
from metrology_process_planner.domains.modes.mode_policies import (
    ModeCapabilities,
    SetupDefinition,
)
from metrology_process_planner.domains.session import ModeDefinition

if __name__ == "__main__":
    unittest.main()


class NonProcessModeValidationTestsPart1(unittest.TestCase):
    def test_non_process_mode_warns_on_recipe_solver_and_process_leaks(self) -> None:
        definition = ModeDefinition(
            "bad_capture",
            "Bad Capture",
            capabilities=ModeCapabilities(supports_process_solver=True),
            setup=SetupDefinition(stage_types=("recipe_context",)),
            artifacts=ArtifactPolicy(
                (ArtifactOutputDefinition("process_output", "stack_image"),)
            ),
            process=ProcessPolicy("forbidden", "line_profile", ""),
            editor=EditorPolicy(
                ("dashboard", "process_outputs"),
                ("stack_image",),
                ("attach_recipe", "regenerate_process_output"),
                process_context_visible=True,
            ),
            reporting=ReportingPolicy(True, ("process_summary", "cross_section", "point_stack")),
        )

        warnings = definition.validation_warnings()

        self.assertTrue(any("solver operation" in warning for warning in warnings))
        self.assertTrue(any("support process solver" in warning for warning in warnings))
        self.assertTrue(any("process outputs" in warning for warning in warnings))
        self.assertTrue(any("process groups" in warning for warning in warnings))
        self.assertTrue(any("process actions" in warning for warning in warnings))
        self.assertTrue(any("process previews" in warning for warning in warnings))
        self.assertTrue(any("hide process context" in warning for warning in warnings))
        self.assertTrue(any("recipe stages" in warning for warning in warnings))
        self.assertTrue(any("process sections" in warning for warning in warnings))
        self.assertTrue(any("cross_section" in warning for warning in warnings))
        self.assertTrue(any("point_stack" in warning for warning in warnings))

    def test_non_process_mode_warns_on_render_profile_without_solver_operation(self) -> None:
        definition = ModeDefinition(
            "bad_render_profile",
            "Bad Render Profile",
            process=ProcessPolicy("forbidden", "none", "profilometry_surface_profile"),
        )

        warnings = definition.validation_warnings()

        self.assertTrue(any("render profile" in warning for warning in warnings))

    def test_non_process_mode_warns_on_alternate_recipe_and_process_terms(self) -> None:
        definition = ModeDefinition(
            "bad_capture",
            "Bad Capture",
            setup=SetupDefinition(stage_types=("recipe_setup", "attach_recipe")),
            process=ProcessPolicy("required", "none", ""),
            editor=EditorPolicy(
                ("dashboard", "process_context", "stack_image"),
                (),
                (),
            ),
            reporting=ReportingPolicy(True, ("process_context", "process_report")),
        )

        warnings = definition.validation_warnings()

        self.assertTrue(any("hide recipe setup" in warning for warning in warnings))
        self.assertTrue(any("recipe_setup" in warning for warning in warnings))
        self.assertTrue(any("attach_recipe" in warning for warning in warnings))
        self.assertTrue(any("process groups" in warning for warning in warnings))
        self.assertTrue(any("process_context" in warning for warning in warnings))
        self.assertTrue(any("stack_image" in warning for warning in warnings))
        self.assertTrue(any("process sections" in warning for warning in warnings))

    def test_non_process_mode_warns_on_generic_artifacts_with_process_roles(self) -> None:
        definition = ModeDefinition(
            "bad_generic_process_artifact",
            "Bad Generic Process Artifact",
            artifacts=ArtifactPolicy(
                (
                    ArtifactOutputDefinition("image", "site_image"),
                    ArtifactOutputDefinition("image", "stack_image"),
                    ArtifactOutputDefinition("svg", "cross_section_image"),
                )
            ),
        )

        warnings = definition.validation_warnings()

        self.assertTrue(any("process outputs" in warning for warning in warnings))
        self.assertTrue(any("stack_image" in warning for warning in warnings))
        self.assertTrue(any("cross_section_image" in warning for warning in warnings))
