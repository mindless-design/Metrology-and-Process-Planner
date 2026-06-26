"""Helpers for recording caught exceptions in diagnostics."""

from __future__ import annotations

import traceback
from typing import Any

from metrology_process_planner.diagnostics.diagnostics_sinks import DiagnosticSink
from metrology_process_planner.diagnostics.trace_context import TraceContext


def exception_payload(
    exc: BaseException,
    message: str,
    *,
    severity: str = "error",
    category: str = "error",
    source_component: str = "",
    operation: str = "",
    remediation_hint: str = "",
    **extra: Any,
) -> dict[str, Any]:
    """Return a diagnostic payload with exception type, message, and stack trace."""

    payload = {
        "message": message,
        "severity": severity,
        "category": category,
        "source_component": source_component,
        "operation": operation,
        "exception_type": type(exc).__name__,
        "exception_message": str(exc),
        "stack_trace": "".join(traceback.format_exception(type(exc), exc, exc.__traceback__)),
        "remediation_hint": remediation_hint,
    }
    payload.update(extra)
    return payload


def emit_exception_event(
    sink: DiagnosticSink | None,
    event_name: str,
    exc: BaseException,
    message: str,
    *,
    session_id: str = "",
    severity: str = "error",
    category: str = "error",
    source_component: str = "",
    operation: str = "",
    remediation_hint: str = "",
    **extra: Any,
) -> None:
    """Emit a structured exception event when a diagnostics sink is available."""

    if sink is None:
        return
    TraceContext.new(session_id, sink).emit(
        event_name,
        exception_payload(
            exc,
            message,
            severity=severity,
            category=category,
            source_component=source_component,
            operation=operation,
            remediation_hint=remediation_hint,
            session_id=session_id,
            **extra,
        ),
    )
