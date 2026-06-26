import unittest

from metrology_process_planner.app.diagnostics import DiagnosticsOpenResult
from metrology_process_planner.diagnostics import DiagnosticEvent
from metrology_process_planner.infrastructure.klayout.diagnostics_shell import (
    KLayoutDiagnosticsWidgetFactory,
)
from metrology_process_planner.ui.diagnostics import DiagnosticsShell
from metrology_process_planner.ui.shell.view_models import EditorActionViewModel
from tests.klayout_widget_fixtures import FakeButton, FakeLabel, FakeVBoxLayout, FakeWidget


class KLayoutDiagnosticsShellTests(unittest.TestCase):
    def test_factory_renders_summary_events_actions_and_callback(self) -> None:
        shell = DiagnosticsShell(KLayoutDiagnosticsWidgetFactory(_FakePya()))
        result = DiagnosticsOpenResult(
            "opened",
            summary_rows=(
                ("Active Session ID", "session-001"),
                ("Report Readiness", "ready"),
            ),
            actions=(
                EditorActionViewModel("ExportDiagnosticsBundle", "Export Bundle"),
                EditorActionViewModel(
                    "CopyCommandTrace",
                    "Copy Trace",
                    enabled=False,
                    disabled_reason="No events.",
                ),
            ),
        )
        event = DiagnosticEvent(
            "Command routed",
            severity="info",
            category="command",
            operation="open_diagnostics",
            event_name="CommandRouted",
        )

        window = shell.open(result, (event,))
        shell.set_action_callback(window, lambda action_id: f"ran:{action_id}")

        state = window._mpp_state
        self.assertTrue(window.shown)
        self.assertEqual("Advanced Diagnostics", window.title)
        self.assertIn("diagnostics_summary", state["qt_regions"])
        self.assertIn("diagnostics_dashboard", state["qt_regions"])
        self.assertIn("Active Session ID | session-001",
                      state["qt_region_labels"]["diagnostics_summary"])
        self.assertIn("Session | Active Session ID | session-001",
                      state["diagnostics_dashboard_rows"])
        self.assertIn("info | command | open_diagnostics | CommandRouted",
                      state["diagnostics_events"])
        self.assertIn("Copy Trace (No events.)", state["diagnostics_action_rows"])
        self.assertEqual("ran:CopyCommandTrace", state["on_action"]("CopyCommandTrace"))


class _FakePya:
    QWidget = FakeWidget
    QVBoxLayout = FakeVBoxLayout
    QLabel = FakeLabel
    QPushButton = FakeButton


if __name__ == "__main__":
    unittest.main()
