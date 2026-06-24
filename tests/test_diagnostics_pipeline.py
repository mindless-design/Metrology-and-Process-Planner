import json
import tempfile
import unittest
from dataclasses import replace
from pathlib import Path

from metrology_process_planner.app.bootstrap import build_app_services
from metrology_process_planner.app.commands import CommandId
from metrology_process_planner.app.diagnostics import AdvancedDiagnosticsController
from metrology_process_planner.domains.geometry import Point
from metrology_process_planner.domains.session import ArtifactStatus, WarningRecord
from metrology_process_planner.infrastructure.diagnostics import (
    DiagnosticsService,
    InMemoryDiagnosticSink,
    JsonlDiagnosticSink,
    TraceContext,
    assert_trace_contains,
    check_pending_to_saved_seam,
    check_session_to_filesystem_seam,
    summarize_trace_timeline,
)
from metrology_process_planner.persistence.paths import SessionPaths
from metrology_process_planner.workflows import (
    CanvasInteractionEngine,
    InteractionContext,
    PendingCaptureReviewService,
)
from tests.editor_render_fixtures import session_without_pending


class DiagnosticsPipelineTests(unittest.TestCase):
    def test_box_capture_and_pending_save_emit_traceable_events(self) -> None:
        sink = InMemoryDiagnosticSink()
        trace = TraceContext.new("session-001", sink)
        engine = CanvasInteractionEngine(sink)
        context = engine.arm_box_capture(InteractionContext(), trace_context=trace)
        started = engine.start_drag(
            session_without_pending(),
            context,
            Point(0, 0),
            True,
            trace_context=trace,
        )
        released = engine.release_drag(
            started.session,
            started.context,
            Point(5, 5),
            True,
            trace_context=trace,
        )
        saved = PendingCaptureReviewService(sink).save_pending_box(
            released.session,
            released.context,
            "pending-001",
            label="Site 1",
            trace_context=trace,
        )

        result = check_pending_to_saved_seam(released.session, saved.session, "pending-001")

        self.assertTrue(result.ok)
        assert_trace_contains(sink, trace.session_trace_id, "PendingCaptureCreated")
        assert_trace_contains(sink, trace.session_trace_id, "CaptureRecordCreated")
        timeline = summarize_trace_timeline(sink, trace.session_trace_id)
        self.assertIn("CaptureRecordCreated", timeline)
        self.assertEqual("cap-002", saved.session.captures[-1].trace_ids["capture_trace_id"])

    def test_missing_artifact_seam_and_debug_bundle_are_structured(self) -> None:
        sink = InMemoryDiagnosticSink()
        source = session_without_pending()

        with tempfile.TemporaryDirectory() as temp_dir:
            paths = SessionPaths.for_folder(Path(temp_dir))
            result = check_session_to_filesystem_seam(source, paths)
            bundle = DiagnosticsService(sink).export_debug_bundle(
                source,
                Path(temp_dir) / "debug-bundle",
                paths,
            )
            report = json.loads((bundle / "seam_check_report.json").read_text())
            self.assertTrue((bundle / "diagnostics" / "events.jsonl").exists())

        self.assertFalse(result.ok)
        self.assertIn("images/cap-001.png", result.missing)
        self.assertIn("session_to_filesystem", report)

    def test_jsonl_sink_and_query_helpers(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            path = Path(temp_dir) / "diagnostics" / "events.jsonl"
            sink = JsonlDiagnosticSink(path)
            trace = TraceContext.new("session-001", sink)

            trace.emit("ExampleEvent", {"message": "hello", "related_record_ids": ("cap-001",)})

            lines = path.read_text(encoding="utf-8").splitlines()

        self.assertEqual(1, len(lines))
        self.assertEqual("ExampleEvent", sink.events_for_item("cap-001")[0].event_name)
        trace_events = sink.events_for_trace(trace.session_trace_id)
        self.assertEqual("ExampleEvent", trace_events[0].event_name)

    def test_advanced_diagnostics_controller_opens_injected_shell(self) -> None:
        sink = InMemoryDiagnosticSink()
        controller = AdvancedDiagnosticsController(sink, DiagnosticsService(sink))
        controller.set_active_session(session_without_pending())

        result = controller.open_current()

        self.assertEqual("opened", result.status)
        self.assertIsNotNone(result.window)

    def test_advanced_diagnostics_controller_raises_existing_window(self) -> None:
        sink = InMemoryDiagnosticSink()
        controller = AdvancedDiagnosticsController(sink, DiagnosticsService(sink))
        controller.set_active_session(session_without_pending())

        first = controller.open_current()
        second = controller.open_current()

        self.assertEqual("opened", first.status)
        self.assertEqual("raised", second.status)
        self.assertIs(first.window, second.window)
        self.assertEqual(1, second.window["raised"])

    def test_diagnostics_summary_shows_session_modes_artifacts_and_commands(self) -> None:
        services = build_app_services()
        source = _session_with_missing_artifact()
        services.diagnostics_controller.set_active_session(source)

        services.command_router.route(CommandId.OPEN_SETUP_GUIDE)
        result = services.diagnostics_controller.open_current()

        summary = dict(result.window["summary"])
        self.assertEqual("Demo (session-001)", summary["Session"])
        self.assertEqual("simple_capture", summary["Mode"])
        self.assertIn("simple_capture", summary["Loaded Modes"])
        self.assertEqual("1 total; missing=1", summary["Artifacts"])
        self.assertEqual("artifact_missing", summary["Warning Codes"])
        self.assertEqual("open_setup_guide", summary["Recent Commands"])
        self.assertIn("CommandRouted", summary["Recent Events"])


def _session_with_missing_artifact():
    source = session_without_pending()
    artifact_id, artifact = next(iter(source.artifacts.items()))
    missing = replace(artifact, status=ArtifactStatus.MISSING)
    return replace(
        source,
        artifacts={artifact_id: missing},
        warnings=(
            WarningRecord(
                "artifact-missing",
                "Missing crop",
                code="artifact_missing",
                related_artifact_refs=(artifact_id,),
            ),
        ),
    )


if __name__ == "__main__":
    unittest.main()
