"""Human-readable trace timeline rendering."""

from __future__ import annotations

from metrology_process_planner.diagnostics.diagnostics_sinks import DiagnosticSink


def summarize_trace_timeline(sink: DiagnosticSink, trace_id: str) -> str:
    """Return a numbered timeline for all events attached to a trace id."""

    events = sink.events_for_trace(trace_id)
    if not events:
        return f"Trace: {trace_id}\n\nNo events found."
    lines = [f"Trace: {trace_id}", ""]
    for index, event in enumerate(events, start=1):
        suffix = f": {event.message}" if event.message != event.event_name else ""
        lines.append(f"{index}. {event.event_name}{suffix}")
    if events[-1].severity in {"warning", "error", "critical"}:
        lines.append("")
        lines.append(f"Last issue: {events[-1].message}")
    return "\n".join(lines)
