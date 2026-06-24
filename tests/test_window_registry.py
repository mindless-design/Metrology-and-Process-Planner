import unittest

from metrology_process_planner.app.window_registry import (
    WindowLifecycleBackend,
    WindowOpenStatus,
    WindowRegistry,
)
from metrology_process_planner.infrastructure.diagnostics import InMemoryDiagnosticSink


class WindowRegistryTests(unittest.TestCase):
    def test_open_or_raise_reuses_live_window(self) -> None:
        backend = _Backend()
        registry: WindowRegistry[dict[str, object]] = WindowRegistry(backend)
        created = registry.open_or_raise(
            "session-editor:demo",
            "Session Editor",
            lambda: {"title": "Session Editor"},
        )
        raised = registry.open_or_raise(
            "session-editor:demo",
            "Session Editor",
            lambda: {"title": "duplicate"},
            refresh_existing=lambda window: window.update({"refreshed": True}),
        )

        self.assertEqual(WindowOpenStatus.CREATED, created.status)
        self.assertEqual(WindowOpenStatus.RAISED, raised.status)
        self.assertIs(created.window, raised.window)
        self.assertEqual(1, backend.raise_count)
        self.assertTrue(raised.window["refreshed"])

    def test_dead_window_is_replaced(self) -> None:
        backend = _Backend(alive=False)
        registry: WindowRegistry[dict[str, object]] = WindowRegistry(backend)
        first = registry.open_or_raise("diagnostics:demo", "Diagnostics", lambda: {"id": 1})
        second = registry.open_or_raise("diagnostics:demo", "Diagnostics", lambda: {"id": 2})

        self.assertNotEqual(first.window, second.window)
        self.assertEqual({"id": 2}, second.window)

    def test_create_failure_returns_failed_result_and_emits_diagnostic(self) -> None:
        sink = InMemoryDiagnosticSink()
        registry: WindowRegistry[dict[str, object]] = WindowRegistry(diagnostic_sink=sink)

        result = registry.open_or_raise(
            "recipe-editor:demo",
            "Recipe Editor",
            _raise_window_error,
        )

        self.assertEqual(WindowOpenStatus.FAILED, result.status)
        self.assertEqual("WindowOpenFailed", sink.events[-1].event_name)
        self.assertEqual("RuntimeError", sink.events[-1].exception_type)

    def test_raise_failure_returns_failed_result_and_keeps_record(self) -> None:
        sink = InMemoryDiagnosticSink()
        backend = _Backend(raise_error=RuntimeError("cannot raise"))
        registry: WindowRegistry[dict[str, object]] = WindowRegistry(backend, sink)
        registry.open_or_raise("setup-guide:demo", "Setup Guide", lambda: {"id": 1})

        result = registry.open_or_raise("setup-guide:demo", "Setup Guide", lambda: {"id": 2})

        self.assertEqual(WindowOpenStatus.FAILED, result.status)
        self.assertEqual("WindowRaiseFailed", sink.events[-1].event_name)
        record = registry.record_for("setup-guide:demo")
        self.assertIsNotNone(record)
        assert record is not None
        self.assertEqual({"id": 1}, record.window)


class _Backend(WindowLifecycleBackend[dict[str, object]]):
    def __init__(
        self,
        *,
        alive: bool = True,
        raise_error: RuntimeError | None = None,
    ) -> None:
        self.alive = alive
        self.raise_error = raise_error
        self.raise_count = 0

    def is_alive(self, window: dict[str, object]) -> bool:
        return self.alive

    def raise_window(self, window: dict[str, object]) -> None:
        self.raise_count += 1
        if self.raise_error is not None:
            raise self.raise_error
        window["raised"] = self.raise_count


def _raise_window_error() -> dict[str, object]:
    raise RuntimeError("cannot open")


if __name__ == "__main__":
    unittest.main()
