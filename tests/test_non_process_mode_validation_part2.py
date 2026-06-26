import unittest

from metrology_process_planner.domains.modes.mode_output_policies import (
    ArtifactOutputDefinition,
    ArtifactPolicy,
)
from metrology_process_planner.domains.session import ModeDefinition

if __name__ == "__main__":
    unittest.main()


class NonProcessModeValidationTestsPart2(unittest.TestCase):
    def test_non_process_mode_warns_on_suffixed_process_artifact_roles(self) -> None:
        definition = ModeDefinition(
            "bad_suffixed_process_artifact",
            "Bad Suffixed Process Artifact",
            artifacts=ArtifactPolicy(
                (
                    ArtifactOutputDefinition("image", "profile_image_spec"),
                    ArtifactOutputDefinition("svg", "cross_section_svg"),
                    ArtifactOutputDefinition("stack_image_png", "legacy_stack"),
                )
            ),
        )

        warnings = definition.validation_warnings()

        self.assertTrue(any("process outputs" in warning for warning in warnings))
        self.assertTrue(any("profile_image_spec" in warning for warning in warnings))
        self.assertTrue(any("cross_section_svg" in warning for warning in warnings))
        self.assertTrue(any("legacy_stack" in warning for warning in warnings))

    def test_non_process_mode_warns_on_external_process_artifact_name_variants(self) -> None:
        definition = ModeDefinition(
            "bad_external_process_artifact_names",
            "Bad External Process Artifact Names",
            artifacts=ArtifactPolicy(
                (
                    ArtifactOutputDefinition("image", "Stack Image PNG"),
                    ArtifactOutputDefinition("CrossSectionImage", "legacyCrossSection"),
                )
            ),
        )

        warnings = definition.validation_warnings()

        self.assertTrue(any("process outputs" in warning for warning in warnings))
        self.assertTrue(any("Stack Image PNG" in warning for warning in warnings))
        self.assertTrue(any("legacyCrossSection" in warning for warning in warnings))

    def test_non_process_mode_warns_on_process_output_manifest_artifact_aliases(self) -> None:
        definition = ModeDefinition(
            "bad_process_manifest_artifacts",
            "Bad Process Manifest Artifacts",
            artifacts=ArtifactPolicy(
                (
                    ArtifactOutputDefinition("process_output_manifest", "manifest"),
                    ArtifactOutputDefinition("json", "process-output-json"),
                    ArtifactOutputDefinition("csv", "Process Output CSV"),
                )
            ),
        )

        warnings = definition.validation_warnings()

        self.assertTrue(any("process outputs" in warning for warning in warnings))
        self.assertTrue(any("manifest" in warning for warning in warnings))
        self.assertTrue(any("process-output-json" in warning for warning in warnings))
        self.assertTrue(any("Process Output CSV" in warning for warning in warnings))
