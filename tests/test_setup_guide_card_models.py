import unittest

from metrology_process_planner.ui.setup_guide import setup_stage_cards
from metrology_process_planner.ui.shell import (
    SetupActionViewModel,
    SetupGuideViewModel,
    SetupStageViewModel,
)


class SetupGuideCardModelTests(unittest.TestCase):
    def test_cards_expose_status_requirement_artifact_and_warning_badges(self) -> None:
        view_model = SetupGuideViewModel(
            "Optical Setup",
            "alignment",
            (
                SetupStageViewModel(
                    "origin",
                    "Origin",
                    "skipped",
                    requirement_badge="optional",
                    artifact_badge="none",
                ),
                SetupStageViewModel(
                    "alignment",
                    "Alignment",
                    "blocked",
                    "Capture Alignment",
                    required=True,
                    artifact_badge="missing",
                    warning_count=2,
                    primary_action_view=SetupActionViewModel(
                        "CaptureAlignment",
                        "Capture Alignment",
                        enabled=False,
                        disabled_reason="Bind a layout first.",
                    ),
                    disabled_reason="Bind a layout first.",
                ),
            ),
            ("CaptureAlignment",),
        )

        cards = {card.stage_id: card for card in setup_stage_cards(view_model)}

        self.assertEqual("Skipped", cards["origin"].status_label)
        self.assertEqual("muted", cards["origin"].status_tone)
        self.assertEqual("Optional", cards["origin"].requirement_label)
        self.assertEqual("No Artifact", cards["origin"].artifact_label)
        self.assertEqual("danger", cards["alignment"].status_tone)
        self.assertEqual("Artifact: Missing", cards["alignment"].artifact_label)
        self.assertEqual("2 Warnings", cards["alignment"].warning_label)
        self.assertTrue(cards["alignment"].active)


if __name__ == "__main__":
    unittest.main()
