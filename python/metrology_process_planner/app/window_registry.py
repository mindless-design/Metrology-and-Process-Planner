"""Modeless application window ownership and diagnostics."""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
from enum import Enum
from typing import Generic, Protocol, TypeVar

from metrology_process_planner.infrastructure.diagnostics_exceptions import emit_exception_event
from metrology_process_planner.infrastructure.diagnostics_models import DiagnosticEvent
from metrology_process_planner.infrastructure.diagnostics_sinks import DiagnosticSink
from metrology_process_planner.infrastructure.trace_context import TraceContext

WindowT = TypeVar("WindowT")
WindowContra = TypeVar("WindowContra", contravariant=True)


class WindowOpenStatus(str, Enum):
    """Outcome for a modeless window open request."""

    CREATED = "created"
    RAISED = "raised"
    FAILED = "failed"


@dataclass(frozen=True)
class WindowRecord(Generic[WindowT]):
    """One tracked modeless application window."""

    key: str
    title: str
    window: WindowT
    revision: int = 1


@dataclass(frozen=True)
class WindowOpenResult(Generic[WindowT]):
    """Result returned after opening or raising a modeless window."""

    status: WindowOpenStatus
    key: str
    title: str = ""
    window: WindowT | None = None
    message: str = ""


class WindowLifecycleBackend(Protocol[WindowContra]):
    """Backend hooks for existing UI toolkits to manage top-level windows."""

    def is_alive(self, window: WindowContra) -> bool:
        """Return whether a tracked window can still be reused."""

    def raise_window(self, window: WindowContra) -> None:
        """Bring an existing window to the front."""


class DefaultWindowLifecycleBackend:
    """Toolkit-neutral lifecycle backend for simple in-memory shells."""

    def is_alive(self, window: object) -> bool:
        """Treat non-None objects as reusable windows."""

        return window is not None

    def raise_window(self, window: object) -> None:
        """Mark in-memory windows as raised when possible."""

        if isinstance(window, dict):
            window["raised"] = int(window.get("raised", 0)) + 1


class WindowRegistry(Generic[WindowT]):
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
            return self._refresh_and_raise(existing, refresh_existing)
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
        self._emit(
            "WindowOpened",
            key,
            title,
            f"Opened modeless window '{title}'.",
            status=WindowOpenStatus.CREATED.value,
        )
        return WindowOpenResult(WindowOpenStatus.CREATED, key, title, window)

    def forget(self, key: str) -> None:
        """Stop tracking a window key after an external close notification."""

        if self._records.pop(key, None) is not None:
            self._emit("WindowForgotten", key, key, f"Stopped tracking '{key}'.")

    def record_for(self, key: str) -> WindowRecord[WindowT] | None:
        """Return the tracked record for a logical window key."""

        return self._records.get(key)

    def keys(self) -> tuple[str, ...]:
        """Return tracked window keys in deterministic order."""

        return tuple(sorted(self._records))

    def _refresh_and_raise(
        self,
        record: WindowRecord[WindowT],
        refresh_existing: Callable[[WindowT], None] | None,
    ) -> WindowOpenResult[WindowT]:
        try:
            if refresh_existing is not None:
                refresh_existing(record.window)
            self._backend.raise_window(record.window)
        except Exception as exc:  # noqa: BLE001 - diagnostics must capture UI failures.
            emit_exception_event(
                self._diagnostic_sink,
                "WindowRaiseFailed",
                exc,
                f"Failed to refresh or raise modeless window '{record.title}'.",
                source_component="app.window_registry",
                operation="open_or_raise",
                remediation_hint="Reopen the window after checking backend raise/render hooks.",
                related_record_ids=(record.key,),
            )
            return WindowOpenResult(
                WindowOpenStatus.FAILED,
                record.key,
                record.title,
                message=f"Failed to raise {record.title}: {exc}",
            )
        self._emit(
            "WindowRaised",
            record.key,
            record.title,
            f"Raised existing modeless window '{record.title}'.",
            status=WindowOpenStatus.RAISED.value,
        )
        return WindowOpenResult(
            WindowOpenStatus.RAISED,
            record.key,
            record.title,
            record.window,
        )

    def _emit(
        self,
        event_name: str,
        key: str,
        title: str,
        message: str,
        *,
        status: str = "",
    ) -> DiagnosticEvent:
        return TraceContext.new(sink=self._diagnostic_sink).emit(
            event_name,
            {
                "message": message,
                "category": "ui",
                "source_component": "app.window_registry",
                "operation": "window_registry",
                "related_record_ids": (key,),
                "after_state_summary": {"key": key, "title": title, "status": status},
            },
        )
