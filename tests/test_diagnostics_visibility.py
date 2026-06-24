import unittest
from dataclasses import replace

from metrology_process_planner.app.bootstrap import build_app_services
from metrology_process_planner.infrastructure.diagnostics import DiagnosticEvent
from metrology_process_planner.workflows.editor import SessionDocumentBuilder
from tests.editor_render_fixtures import session as rich_session
from tests.editor_render_fixtures import session_without_pending


class DiagnosticsVisibilityTests(unittest.TestCase):
    def test_summary_includes_current_editor_and_canvas_selection(self) -> None:
        services = build_app_services()
        document = SessionDocumentBuilder().build(rich_session())
        editor_result = services.session_editor_controller.open_document(document)
        editor_result.window["on_select"]("capture:cap-001")
        selected = services.session_editor_controller.current_document
        self.assertIsNotNone(selected)
        services.diagnostics_controller.set_active_session(selected.session)

        result = services.diagnostics_controller.open_current()

        summary = dict(result.window["summary"])
        self.assertEqual(
            "Site 1 (capture:cap-001, ready)",
            summary["Selected Editor Item"],
        )
        self.assertEqual("canvas-cap", summary["Selected Canvas Object"])

    def test_summary_includes_mode_validation_and_recent_failures(self) -> None:
        services = build_app_services()
        source = replace(
            session_without_pending(),
            extensions={
                "mode_validation": {
                    "requested_mode": "future_mode",
                    "fallback_mode": "simple_capture",
                    "status": "unsupported",
                }
            },
        )
        services.diagnostics_controller.set_active_session(source)
        services.diagnostics_sink.emit(
            DiagnosticEvent(
                "Session save failed",
                severity="error",
                category="persistence",
                event_name="SessionSaveFailed",
                operation="save_session",
                exception_type="OSError",
                exception_message="disk full",
            )
        )

        result = services.diagnostics_controller.open_current()

        summary = dict(result.window["summary"])
        self.assertEqual("unsupported: future_mode -> simple_capture", summary["Mode Validation"])
        self.assertEqual("save_session: disk full", summary["Recent Failures"])


if __name__ == "__main__":
    unittest.main()
