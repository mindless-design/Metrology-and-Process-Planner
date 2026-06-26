import unittest
from dataclasses import replace

from metrology_process_planner.domains.session import SessionMode
from metrology_process_planner.domains.warnings.warning_visibility import session_is_process_aware
from tests.editor_render_fixtures import session_without_pending


class ModeProcessAwarenessTests(unittest.TestCase):
    def test_shared_process_awareness_predicate_matches_mode_policy(self) -> None:
        base = session_without_pending()
        non_process_modes = (
            SessionMode.SIMPLE_CAPTURE,
            SessionMode.FAST_BATCH_CAPTURE,
            SessionMode.CAD_REVIEW,
            SessionMode.OPTICAL_METROLOGY,
            SessionMode.CDSEM_MEASUREMENT,
            SessionMode.GRID_MEASUREMENT,
        )

        for mode in non_process_modes:
            with self.subTest(mode=mode.value):
                self.assertFalse(session_is_process_aware(replace(base, mode=mode)))
        self.assertTrue(
            session_is_process_aware(replace(base, mode=SessionMode.PROFILOMETRY_PLANNER))
        )


if __name__ == "__main__":
    unittest.main()
