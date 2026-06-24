import unittest
from pathlib import Path

from metrology_process_planner.infrastructure.diagnostics import (
    DiagnosticEvent,
    ListDiagnosticSink,
    build_diagnostics_snapshot,
)


class DiagnosticsTests(unittest.TestCase):
    def test_diagnostics_snapshot_serializes_core_context(self) -> None:
        snapshot = build_diagnostics_snapshot(Path.cwd(), (DiagnosticEvent("ok"),))
        data = snapshot.to_dict()

        self.assertEqual("0.1.0", data["plugin_version"])
        self.assertIn("package_root", data)
        self.assertIn("python_root", data)
        self.assertEqual("ok", data["events"][0]["message"])
        self.assertEqual("info", data["events"][0]["severity"])
        self.assertEqual("core", data["events"][0]["source_component"])

    def test_list_sink_can_produce_snapshot(self) -> None:
        sink = ListDiagnosticSink()
        sink.emit(DiagnosticEvent("warning", severity="warning", source="test"))

        snapshot = sink.snapshot(Path.cwd())

        self.assertEqual("warning", snapshot.events[0].message)


if __name__ == "__main__":
    unittest.main()
