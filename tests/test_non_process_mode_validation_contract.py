import unittest

from metrology_process_planner.domains.modes.mode_output_policies import (
    EditorPolicy,
    ReportingPolicy,
)
from metrology_process_planner.domains.modes.mode_policies import SetupDefinition
from metrology_process_planner.domains.modes.mode_registry import ModeDefinition


class NonProcessModeValidationContractTests(unittest.TestCase):
    def test_non_process_mode_validation_rejects_recipe_setup_stages(self) -> None:
        definition = ModeDefinition(
            "bad_recipe_setup",
            "Bad Recipe Setup",
            setup=SetupDefinition(stage_types=("origin_choice", "attach_recipe")),
        )

        warnings = definition.validation_warnings()

        self.assertTrue(any("recipe stages" in warning for warning in warnings))

    def test_non_process_mode_validation_rejects_process_report_sections(self) -> None:
        definition = ModeDefinition(
            "bad_process_report",
            "Bad Process Report",
            reporting=ReportingPolicy(
                enabled=True,
                sections=("capture_summary", "stack_summary"),
            ),
        )

        warnings = definition.validation_warnings()

        self.assertTrue(any("process sections" in warning for warning in warnings))

    def test_non_process_mode_validation_rejects_cross_section_group_alias(self) -> None:
        definition = ModeDefinition(
            "bad_cross_section_group",
            "Bad Cross Section Group",
            editor=EditorPolicy(navigator_groups=("dashboard", "cross_sections")),
        )

        warnings = definition.validation_warnings()

        self.assertTrue(any("process groups" in warning for warning in warnings))
        self.assertTrue(any("cross_sections" in warning for warning in warnings))

    def test_non_process_mode_validation_normalizes_external_policy_names(self) -> None:
        definition = ModeDefinition(
            "bad_external_policy_names",
            "Bad External Policy Names",
            setup=SetupDefinition(stage_types=("origin_choice", "Recipe Setup")),
            editor=EditorPolicy(
                navigator_groups=("dashboard", "Process Outputs"),
                preview_modes=("Stack Image",),
                actions=("AttachRecipe", "regenerate-process-output"),
            ),
            reporting=ReportingPolicy(
                enabled=True,
                sections=("cross-section-gallery",),
            ),
        )

        warnings = definition.validation_warnings()

        self.assertTrue(any("recipe stages" in warning for warning in warnings))
        self.assertTrue(any("process groups" in warning for warning in warnings))
        self.assertTrue(any("process previews" in warning for warning in warnings))
        self.assertTrue(any("process actions" in warning for warning in warnings))
        self.assertTrue(any("process sections" in warning for warning in warnings))


if __name__ == "__main__":
    unittest.main()
