import unittest

from metrology_process_planner.app.window_registry import (
    WindowLifecycleBackend,
    WindowOpenStatus,
    WindowRegistry,
    surface_key,
)
from metrology_process_planner.diagnostics import InMemoryDiagnosticSink


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

    def test_lifecycle_methods_refresh_raise_close_and_report_open_state(self) -> None:
        registry: WindowRegistry[dict[str, object]] = WindowRegistry()
        registry.open_or_raise("recipe-editor:demo", "Recipe Editor", lambda: {"id": 1})

        refreshed = registry.refresh(
            "recipe-editor:demo",
            lambda window: window.update({"view_model": "fresh"}),
        )
        raised = registry.bring_to_front("recipe-editor:demo")
        closed = registry.close("recipe-editor:demo")

        self.assertTrue(refreshed)
        self.assertEqual(WindowOpenStatus.RAISED, raised.status)
        self.assertTrue(closed)
        self.assertFalse(registry.is_open("recipe-editor:demo"))

    def test_named_surface_methods_use_stable_product_keys(self) -> None:
        registry: WindowRegistry[dict[str, object]] = WindowRegistry()

        editor = registry.get_or_create_session_editor(
            "session-001",
            "Session Editor",
            lambda: {"surface": "editor"},
        )
        setup = registry.get_or_create_setup_guide(
            "session-001",
            "Setup Guide",
            lambda: {"surface": "setup"},
        )
        recipe = registry.get_or_create_recipe_editor(
            "recipe-001",
            "Recipe Editor",
            lambda: {"surface": "recipe"},
        )
        diagnostics = registry.get_or_create_diagnostics_panel(
            "session-001",
            "Advanced Diagnostics",
            lambda: {"surface": "diagnostics"},
        )

        self.assertEqual("session-editor:session-001", editor.key)
        self.assertEqual("setup-guide:session-001", setup.key)
        self.assertEqual("recipe-editor:recipe-001", recipe.key)
        self.assertEqual("advanced-diagnostics:session-001", diagnostics.key)
        self.assertEqual(
            (
                "advanced-diagnostics:session-001",
                "recipe-editor:recipe-001",
                "session-editor:session-001",
                "setup-guide:session-001",
            ),
            registry.keys(),
        )

    def test_named_surface_refreshes_existing_window(self) -> None:
        registry: WindowRegistry[dict[str, object]] = WindowRegistry()
        first = registry.get_or_create_session_editor(
            "session-001",
            "Session Editor",
            lambda: {"revision": 1},
        )
        second = registry.get_or_create_session_editor(
            "session-001",
            "Session Editor",
            lambda: {"revision": 2},
            refresh_existing=lambda window: window.update({"revision": 3}),
        )

        self.assertEqual(WindowOpenStatus.CREATED, first.status)
        self.assertEqual(WindowOpenStatus.RAISED, second.status)
        self.assertIs(first.window, second.window)
        self.assertEqual(3, second.window["revision"])

    def test_surface_key_normalizes_blank_owner_ids(self) -> None:
        self.assertEqual("setup-guide:none", surface_key("setup-guide", ""))


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
