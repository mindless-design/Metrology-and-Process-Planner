"""Trace context passed through workflows and service calls."""

from __future__ import annotations

from dataclasses import dataclass, replace
from typing import Any, Optional
from uuid import uuid4

from metrology_process_planner.infrastructure.diagnostics_models import DiagnosticEvent
from metrology_process_planner.infrastructure.diagnostics_sinks import DiagnosticSink


@dataclass(frozen=True)
class TraceContext:
    """Runtime trace identifiers and optional diagnostic sink."""

    session_trace_id: str = ""
    workflow_trace_id: str = ""
    command_trace_id: str = ""
    parent_event_id: str = ""
    active_item_id: str = ""
    active_canvas_object_id: str = ""
    mode_id: str = ""
    source_view_id: str = ""
    debug_enabled: bool = True
    sink: Optional[DiagnosticSink] = None

    @classmethod
    def new(cls, session_id: str = "", sink: Optional[DiagnosticSink] = None) -> TraceContext:
        """Create a trace context with stable session and workflow ids."""

        return cls(
            session_trace_id=session_id or _trace_id("session"),
            workflow_trace_id=_trace_id("workflow"),
            sink=sink,
        )

    def child(self, operation_name: str) -> TraceContext:
        """Return a child context for an operation."""

        return replace(self, command_trace_id=_trace_id(operation_name))

    def with_item(self, item_id: str) -> TraceContext:
        """Return a context focused on an editor item."""

        return replace(self, active_item_id=item_id)

    def with_canvas_object(self, canvas_object_id: str) -> TraceContext:
        """Return a context focused on a canvas object."""

        return replace(self, active_canvas_object_id=canvas_object_id)

    def with_command(self, command_id: str) -> TraceContext:
        """Return a context focused on a command."""

        return replace(self, command_trace_id=command_id)

    def emit(self, event_name: str, payload: Optional[dict[str, Any]] = None) -> DiagnosticEvent:
        """Emit a structured diagnostic event through the attached sink."""

        event = diagnostic_event_from_context(self, event_name, payload or {})
        if self.debug_enabled and self.sink is not None:
            self.sink.emit(event)
        return event


def diagnostic_event_from_context(
    context: TraceContext,
    event_name: str,
    payload: dict[str, Any],
) -> DiagnosticEvent:
    """Build a diagnostic event from trace context and payload."""

    trace_ids = {
        "session_trace_id": context.session_trace_id,
        "workflow_trace_id": context.workflow_trace_id,
        "command_trace_id": context.command_trace_id,
    }
    if context.active_item_id:
        trace_ids["editor_item_trace_id"] = context.active_item_id
    if context.active_canvas_object_id:
        trace_ids["canvas_object_trace_id"] = context.active_canvas_object_id
    return DiagnosticEvent(
        message=str(payload.get("message", event_name)),
        severity=str(payload.get("severity", "info")),
        source=str(payload.get("source_component", payload.get("source", "workflow"))),
        event_name=event_name,
        category=str(payload.get("category", "workflow")),
        operation=str(payload.get("operation", event_name)),
        session_id=str(payload.get("session_id", "")),
        trace_ids={key: value for key, value in trace_ids.items() if value},
        before_state_summary=payload.get("before_state_summary"),
        after_state_summary=payload.get("after_state_summary"),
        expected=payload.get("expected"),
        actual=payload.get("actual"),
        related_record_ids=tuple(str(item) for item in payload.get("related_record_ids", ())),
        related_artifact_paths=tuple(
            str(item) for item in payload.get("related_artifact_paths", ())
        ),
        exception_type=str(payload.get("exception_type", "")),
        exception_message=str(payload.get("exception_message", "")),
        stack_trace=str(payload.get("stack_trace", "")),
        user_visible_warning_id=str(payload.get("user_visible_warning_id", "")),
        remediation_hint=str(payload.get("remediation_hint", "")),
    )


def _trace_id(prefix: str) -> str:
    return f"{prefix.replace(' ', '_')}_{uuid4().hex[:12]}"
