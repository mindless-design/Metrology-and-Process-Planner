"""Modeless application window ownership and diagnostics."""

from __future__ import annotations

from collections.abc import Callable, Iterator
from typing import Generic, TypeVar

from metrology_process_planner.app.window_registry_support import (
    emit_window_event,
    refresh_and_raise,
)
from metrology_process_planner.app.window_registry_surfaces import (
    WindowSurfaceMixin,
    surface_key,
)
from metrology_process_planner.app.window_registry_types import (
    WindowLifecycleBackend,
    WindowOpenResult,
    WindowOpenStatus,
    WindowRecord,
)
from metrology_process_planner.diagnostics.diagnostics_exceptions import emit_exception_event
from metrology_process_planner.diagnostics.diagnostics_sinks import DiagnosticSink

WindowT = TypeVar("WindowT")


class DefaultWindowLifecycleBackend:
    """Toolkit-neutral lifecycle backend for simple in-memory shells."""

    def is_alive(self, window: object) -> bool:
        """Treat non-None objects as reusable windows."""

        return window is not None

    def raise_window(self, window: object) -> None:
        """Mark in-memory windows as raised when possible."""

        if isinstance(window, dict):
            window["raised"] = int(window.get("raised", 0)) + 1


class WindowRegistry(WindowSurfaceMixin[WindowT], Generic[WindowT]):
    """Own modeless windows by logical key and prevent duplicate surfaces."""

    def __init__(
        self,
        backend: WindowLifecycleBackend[WindowT] | None = None,
        diagnostic_sink: DiagnosticSink | None = None,
    ) -> None:
        self._backend = backend if backend is not None else DefaultWindowLifecycleBackend()
        self._diagnostic_sink = diagnostic_sink
        self._records: dict[str, WindowRecord[WindowT]] = {}

    def open_or_raise(
        self,
        key: str,
        title: str,
        create: Callable[[], WindowT],
        *,
        refresh_existing: Callable[[WindowT], None] | None = None,
    ) -> WindowOpenResult[WindowT]:
        """Create a modeless window or raise the live one for the same key."""

        existing = self._records.get(key)
        if existing is not None and self._backend.is_alive(existing.window):
            return refresh_and_raise(
                self._backend,
                self._diagnostic_sink,
                existing,
                refresh_existing,
            )
        self._records.pop(key, None)
        try:
            window = create()
        except Exception as exc:  # noqa: BLE001 - diagnostics must capture UI failures.
            emit_exception_event(
                self._diagnostic_sink,
                "WindowOpenFailed",
                exc,
                f"Failed to open modeless window '{title}'.",
                source_component="app.window_registry",
                operation="open_or_raise",
                remediation_hint="Review the window backend and shell construction path.",
                related_record_ids=(key,),
            )
            return WindowOpenResult(
                WindowOpenStatus.FAILED,
                key,
                title,
                message=f"Failed to open {title}: {exc}",
            )
        record = WindowRecord(key, title, window)
        self._records[key] = record
        emit_window_event(
            self._diagnostic_sink,
            "WindowOpened",
            key,
            title,
            f"Opened modeless window '{title}'.",
            WindowOpenStatus.CREATED.value,
        )
        return WindowOpenResult(WindowOpenStatus.CREATED, key, title, window)

    def forget(self, key: str) -> None:
        """Stop tracking a window key after an external close notification."""

        if self._records.pop(key, None) is not None:
            emit_window_event(
                self._diagnostic_sink,
                "WindowForgotten",
                key,
                key,
                f"Stopped tracking '{key}'.",
            )

    def close(self, key: str) -> bool:
        """Close or forget a modeless window key."""

        existed = key in self._records
        self.forget(key)
        return existed

    def is_open(self, key: str) -> bool:
        """Return whether a live window exists for a logical key."""

        record = self._records.get(key)
        return bool(record is not None and self._backend.is_alive(record.window))

    def bring_to_front(self, key: str) -> WindowOpenResult[WindowT]:
        """Raise an existing modeless window without creating a new one."""

        record = self._records.get(key)
        if record is None or not self._backend.is_alive(record.window):
            return WindowOpenResult(WindowOpenStatus.FAILED, key, message="Window is not open.")
        return refresh_and_raise(self._backend, self._diagnostic_sink, record, None)

    def refresh(self, key: str, render: Callable[[WindowT], None]) -> bool:
        """Render fresh view-model state into an existing live window."""

        record = self._records.get(key)
        if record is None or not self._backend.is_alive(record.window):
            return False
        render(record.window)
        return True

    def record_for(self, key: str) -> WindowRecord[WindowT] | None:
        """Return the tracked record for a logical window key."""

        return self._records.get(key)

    def keys(self) -> tuple[str, ...]:
        """Return tracked window keys in deterministic order."""

        return tuple(sorted(self._records))

    def __iter__(self) -> Iterator[str]:
        """Iterate tracked window keys in deterministic order."""

        return iter(self.keys())


__all__ = [
    "DefaultWindowLifecycleBackend",
    "surface_key",
    "WindowLifecycleBackend",
    "WindowOpenResult",
    "WindowOpenStatus",
    "WindowRecord",
    "WindowRegistry",
]
