import unittest

from metrology_process_planner.infrastructure.klayout.setup_guide_shell import (
    KLayoutSetupGuideSurfaceFactory,
)
from metrology_process_planner.ui.modeless import ModelessSurfaceShell
from metrology_process_planner.ui.shell import SetupGuideViewModel, SetupStageViewModel
from tests.klayout_widget_fixtures import FakeButton, FakeLabel, FakeVBoxLayout, FakeWidget


class KLayoutSetupGuideShellTests(unittest.TestCase):
    def test_factory_renders_setup_stage_cards_into_qt_state(self) -> None:
        view_model = SetupGuideViewModel(
            "CDSEM Setup",
            "sem_alignment",
            (
                SetupStageViewModel(
                    "sem_alignment",
                    "SEM Alignment",
                    "active",
                    "Capture SEM Alignment",
                    artifact_badge="present",
                ),
            ),
            ("CaptureSemAlignment",),
            mode_display_name="CDSEM Measurement",
            status_message="Capture the SEM alignment mark.",
        )

        window = ModelessSurfaceShell(KLayoutSetupGuideSurfaceFactory(_FakePya())).open(
            "Setup Guide - CDSEM Setup",
            view_model,
        )
        state = window._mpp_state

        self.assertTrue(window.shown)
        self.assertEqual("Setup Guide - CDSEM Setup", window.title)
        self.assertEqual("SEM Alignment", state["setup_stage_cards"][0].title)
        self.assertEqual("accent", state["setup_stage_cards"][0].status_tone)
        self.assertIn(
            "SEM Alignment | Active | Required | Artifact: Present",
            state["qt_region_labels"]["setup_stage_cards"][0],
        )


class _FakePya:
    QWidget = FakeWidget
    QVBoxLayout = FakeVBoxLayout
    QLabel = FakeLabel
    QPushButton = FakeButton


if __name__ == "__main__":
    unittest.main()
