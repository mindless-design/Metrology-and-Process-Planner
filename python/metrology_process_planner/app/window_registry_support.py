"""Support helpers for modeless window registry diagnostics."""

from __future__ import annotations

from collections.abc import Callable
from typing import TypeVar

from metrology_process_planner.app.window_registry_types import (
    WindowLifecycleBackend,
    WindowOpenResult,
    WindowOpenStatus,
    WindowRecord,
)
from metrology_process_planner.infrastructure.diagnostics_exceptions import emit_exception_event
from metrology_process_planner.infrastructure.diagnostics_models import DiagnosticEvent
from metrology_process_planner.infrastructure.diagnostics_sinks import DiagnosticSink
from metrology_process_planner.infrastructure.trace_context import TraceContext

WindowT = TypeVar("WindowT")


def refresh_and_raise(
    backend: WindowLifecycleBackend[WindowT],
    sink: DiagnosticSink | None,
    record: WindowRecord[WindowT],
    refresh_existing: Callable[[WindowT], None] | None,
) -> WindowOpenResult[WindowT]:
    """Refresh and raise an existing modeless window with diagnostics."""

    try:
        if refresh_existing is not None:
            refresh_existing(record.window)
        backend.raise_window(record.window)
    except Exception as exc:  # noqa: BLE001 - diagnostics must capture UI failures.
        emit_exception_event(
            sink,
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
    emit_window_event(
        sink,
        "WindowRaised",
        record.key,
        record.title,
        f"Raised existing modeless window '{record.title}'.",
        WindowOpenStatus.RAISED.value,
    )
    return WindowOpenResult(WindowOpenStatus.RAISED, record.key, record.title, record.window)


def emit_window_event(
    sink: DiagnosticSink | None,
    event_name: str,
    key: str,
    title: str,
    message: str,
    status: str = "",
) -> DiagnosticEvent:
    """Emit a structured window lifecycle event."""

    return TraceContext.new(sink=sink).emit(
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
