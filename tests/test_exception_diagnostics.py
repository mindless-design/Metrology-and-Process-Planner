import tempfile
import unittest
from pathlib import Path

from metrology_process_planner.app.commands import CommandId, CommandRegistry
from metrology_process_planner.diagnostics import InMemoryDiagnosticSink
from metrology_process_planner.persistence.json_store import SessionJsonStore
from metrology_process_planner.persistence.paths import SessionPaths
from metrology_process_planner.ui.shell.command_router import CommandRouter
from metrology_process_planner.workflows.editor import (
    DrawingOwnerRef,
    RenderRefreshRequest,
    RenderTarget,
    SessionRenderBridge,
)
from tests.editor_render_fixtures import FailingRasterizer, session_without_pending


class ExceptionDiagnosticsTests(unittest.TestCase):
    def test_command_router_records_exception_details(self) -> None:
        sink = InMemoryDiagnosticSink()
        registry = CommandRegistry()

        def fail() -> None:
            raise ValueError("adapter exploded")

        registry.register(CommandId.OPEN_SESSION_EDITOR, fail)
        result = CommandRouter(registry, sink).route(CommandId.OPEN_SESSION_EDITOR)
        event = sink.recent(1)[0]

        self.assertEqual("error", result.status)
        self.assertEqual("CommandRouted", event.event_name)
        self.assertEqual("ValueError", event.exception_type)
        self.assertIn("adapter exploded", event.exception_message)
        self.assertIn("Traceback", event.stack_trace)

    def test_json_store_records_save_failures(self) -> None:
        sink = InMemoryDiagnosticSink()
        source = session_without_pending()

        with tempfile.TemporaryDirectory() as temp_dir:
            blocker = Path(temp_dir) / "not-a-folder"
            blocker.write_text("occupied", encoding="utf-8")

            with self.assertRaises(OSError):
                SessionJsonStore(sink).save(source, SessionPaths.for_folder(blocker))

        event = sink.recent(1)[0]
        self.assertEqual("JsonWriteFailed", event.event_name)
        self.assertTrue(event.exception_type)
        self.assertIn("session.json", event.related_artifact_paths[0])

    def test_rasterizer_failure_records_exception_details(self) -> None:
        sink = InMemoryDiagnosticSink()
        target = RenderRefreshRequest(
            targets=(RenderTarget(DrawingOwnerRef("capture", "cap-001")),)
        )

        with tempfile.TemporaryDirectory() as temp_dir:
            SessionRenderBridge(
                SessionPaths.for_folder(Path(temp_dir)),
                rasterizer=FailingRasterizer(),
                diagnostic_sink=sink,
            ).refresh(session_without_pending(), target)

        event = [
            item for item in sink.events if item.event_name == "ArtifactRasterizationWarning"
        ][0]
        self.assertEqual("RuntimeError", event.exception_type)
        self.assertIn("Traceback", event.stack_trace)


if __name__ == "__main__":
    unittest.main()
