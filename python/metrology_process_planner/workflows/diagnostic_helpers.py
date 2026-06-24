"""Small diagnostic helpers shared by workflow services."""

from __future__ import annotations

from typing import Optional

from metrology_process_planner.infrastructure.diagnostics_sinks import DiagnosticSink
from metrology_process_planner.infrastructure.trace_context import TraceContext


def emit_trace_event(
    sink: Optional[DiagnosticSink],
    trace_context: Optional[TraceContext],
    event_name: str,
    message: str,
    category: str,
    source_component: str,
    severity: str = "info",
    related_record_ids: tuple[str, ...] = (),
    related_artifact_paths: tuple[str, ...] = (),
) -> None:
    """Emit a structured trace event if diagnostics are available."""

    context = trace_context or (TraceContext.new(sink=sink) if sink is not None else None)
    if context is None:
        return
    context.emit(
        event_name,
        {
            "message": message,
            "severity": severity,
            "category": category,
            "source_component": source_component,
            "related_record_ids": related_record_ids,
            "related_artifact_paths": related_artifact_paths,
        },
    )


def trace_ids(trace_context: Optional[TraceContext], **extra: str) -> dict[str, str]:
    """Return persisted trace ids derived from a runtime context."""

    ids = dict(extra)
    if trace_context is not None:
        ids.update(
            {
                "session_trace_id": trace_context.session_trace_id,
                "workflow_trace_id": trace_context.workflow_trace_id,
                "command_trace_id": trace_context.command_trace_id,
            }
        )
    return {key: value for key, value in ids.items() if value}
