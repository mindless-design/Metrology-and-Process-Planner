import unittest
from dataclasses import replace

from metrology_process_planner.app.diagnostics_summary import diagnostics_summary_rows
from metrology_process_planner.domains.session import (
    SessionMode,
    SetupItemRecord,
    SetupState,
    built_in_mode_registry,
)
from tests.editor_render_fixtures import session_without_pending


class DiagnosticsSetupStateTests(unittest.TestCase):
    def test_mode_required_setup_reports_incomplete_before_items_exist(self) -> None:
        for mode in (SessionMode.OPTICAL_METROLOGY, SessionMode.CDSEM_MEASUREMENT):
            with self.subTest(mode=mode.value):
                rows = dict(
                    diagnostics_summary_rows(
                        replace(session_without_pending(), mode=mode, setup=SetupState()),
                        (),
                        built_in_mode_registry(),
                    )
                )

                self.assertIn("incomplete", rows["Setup State"])
                self.assertNotEqual("not_required", rows["Setup State"])

    def test_valid_ready_flag_reports_ready_with_unfinished_optional_cards(self) -> None:
        rows = dict(
            diagnostics_summary_rows(
                replace(
                    session_without_pending(),
                    mode=SessionMode.OPTICAL_METROLOGY,
                    setup=SetupState(
                        is_capture_ready=True,
                        items=(_complete_alignment("optical_alignment"),),
                    ),
                ),
                (),
                built_in_mode_registry(),
            )
        )

        self.assertEqual("ready", rows["Setup State"])

    def test_stale_ready_flag_reports_incomplete_when_required_setup_is_missing(self) -> None:
        rows = dict(
            diagnostics_summary_rows(
                replace(
                    session_without_pending(),
                    mode=SessionMode.CDSEM_MEASUREMENT,
                    setup=SetupState(
                        is_capture_ready=True,
                        items=(_complete_alignment("optical_alignment"),),
                    ),
                ),
                (),
                built_in_mode_registry(),
            )
        )

        self.assertIn("incomplete", rows["Setup State"])


def _complete_alignment(item_id: str) -> SetupItemRecord:
    item_type = (
        "sem_alignment_box_capture"
        if item_id == "sem_alignment"
        else "alignment_box_capture"
    )
    label = "SEM Alignment Mark" if item_id == "sem_alignment" else "Optical Alignment Mark"
    return SetupItemRecord(
        item_id,
        item_type,
        label,
        "complete",
        metadata={"required": True},
    )


if __name__ == "__main__":
    unittest.main()
