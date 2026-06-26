import unittest
from dataclasses import replace
from pathlib import Path
from tempfile import TemporaryDirectory

from metrology_process_planner.app.bootstrap import build_app_services
from metrology_process_planner.diagnostics import (
    DiagnosticEvent,
)
from metrology_process_planner.domains.session import (
    SessionMode,
)
from metrology_process_planner.domains.session.workflow import WorkflowState
from metrology_process_planner.persistence.paths import SessionPaths
from metrology_process_planner.workflows.editor import (
    SessionDocumentBuilder,
    mark_pending_dirty,
)
from tests.editor_render_fixtures import session as rich_session
from tests.editor_render_fixtures import session_without_pending

if __name__ == "__main__":
    unittest.main()


class DiagnosticsVisibilityTestsPart1(unittest.TestCase):
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
        self.assertIn("record=cap-001, item=capture:cap-001", summary["Active Canvas Object"])

    def test_summary_includes_dashboard_context_rows(self) -> None:
        services = build_app_services()
        with TemporaryDirectory() as temp_dir:
            paths = SessionPaths.for_folder(Path(temp_dir))
            document = mark_pending_dirty(SessionDocumentBuilder().build(rich_session()))
            document = replace(document, loaded_path=paths.session_json)
            services.session_editor_controller.open_document(document)
            current = services.session_editor_controller.current_document
            self.assertIsNotNone(current)
            services.diagnostics_controller.set_active_session(current.session, paths)

            result = services.diagnostics_controller.open_current()

        summary = dict(result.window["summary"])
        self.assertEqual("session-001", summary["Active Session ID"])
        self.assertEqual(str(paths.session_json), summary["Active Session Path"])
        self.assertEqual("dirty", summary["Dirty State"])
        self.assertEqual("simple_capture", summary["Active Mode"])
        self.assertEqual("none", summary["Solver Backend"])
        self.assertEqual("default", summary["Renderer Backend"])
        self.assertIn("Report Readiness", summary)

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

    def test_summary_includes_recipe_free_workflow_state_rows(self) -> None:
        services = build_app_services()
        source = replace(
            session_without_pending(),
            mode=SessionMode.OPTICAL_METROLOGY,
            workflow=WorkflowState(
                active=True,
                stage="measurement_line",
                active_primitive="line",
                pending_item_ref="measurement:cap-001",
            ),
        )
        services.diagnostics_controller.set_active_session(source)

        result = services.diagnostics_controller.open_current()

        summary = dict(result.window["summary"])
        self.assertEqual("measurement_line", summary["Workflow State"])
        self.assertEqual("incomplete (1/5 complete)", summary["Setup State"])
        self.assertEqual("armed_line", summary["Capture State"])
        self.assertEqual("armed_line", summary["Measurement Workflow"])
        self.assertEqual("line", summary["Armed Capture Tool"])
