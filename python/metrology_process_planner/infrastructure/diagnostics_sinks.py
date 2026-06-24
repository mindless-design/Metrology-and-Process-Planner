"""Diagnostic event sink implementations."""

from __future__ import annotations

import json
from pathlib import Path
from typing import TYPE_CHECKING, Any, Protocol

from metrology_process_planner.infrastructure.diagnostics_models import DiagnosticEvent

if TYPE_CHECKING:
    from metrology_process_planner.infrastructure.diagnostics_models import DiagnosticsSnapshot


class DiagnosticSink(Protocol):
    """Receiver and query surface for structured diagnostic events."""

    def emit(self, event: DiagnosticEvent) -> None:
        """Record one diagnostic event."""

    def query(self, filters: dict[str, Any]) -> tuple[DiagnosticEvent, ...]:
        """Return events matching simple equality filters."""

    def recent(self, limit: int) -> tuple[DiagnosticEvent, ...]:
        """Return the most recent events."""

    def events_for_trace(self, trace_id: str) -> tuple[DiagnosticEvent, ...]:
        """Return events that mention a trace id."""

    def events_for_item(self, item_id: str) -> tuple[DiagnosticEvent, ...]:
        """Return events related to an editor item or record id."""

    def events_for_artifact(self, path: str) -> tuple[DiagnosticEvent, ...]:
        """Return events related to an artifact path."""

    def export_json(self, path: Path) -> Path:
        """Write events to JSON and return the destination."""

    def clear(self) -> None:
        """Clear runtime events when supported."""


class InMemoryDiagnosticSink:
    """In-memory sink useful for tests and runtime diagnostics panels."""

    def __init__(self) -> None:
        self.events: list[DiagnosticEvent] = []

    def emit(self, event: DiagnosticEvent) -> None:
        """Store a diagnostic event in memory."""

        self.events.append(event)

    def query(self, filters: dict[str, Any]) -> tuple[DiagnosticEvent, ...]:
        """Return events matching simple equality filters."""

        return tuple(event for event in self.events if _matches(event, filters))

    def recent(self, limit: int) -> tuple[DiagnosticEvent, ...]:
        """Return the most recent events."""

        return tuple(self.events[-limit:])

    def events_for_trace(self, trace_id: str) -> tuple[DiagnosticEvent, ...]:
        """Return events that mention a trace id."""

        return tuple(event for event in self.events if trace_id in event.trace_ids.values())

    def events_for_item(self, item_id: str) -> tuple[DiagnosticEvent, ...]:
        """Return events related to an item or record id."""

        return tuple(event for event in self.events if item_id in event.related_record_ids)

    def events_for_artifact(self, path: str) -> tuple[DiagnosticEvent, ...]:
        """Return events related to an artifact path."""

        return tuple(event for event in self.events if path in event.related_artifact_paths)

    def export_json(self, path: Path) -> Path:
        """Write events to JSON and return the destination."""

        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps([event.to_dict() for event in self.events], indent=2))
        return path

    def clear(self) -> None:
        """Clear runtime events."""

        self.events.clear()

    def snapshot(self, package_root: Path) -> DiagnosticsSnapshot:
        """Return a diagnostics snapshot for tests and debug bundles."""

        from metrology_process_planner.infrastructure.diagnostics_snapshots import (
            build_diagnostics_snapshot,
        )

        return build_diagnostics_snapshot(package_root, tuple(self.events))


class JsonlDiagnosticSink:
    """Append diagnostic events as JSONL for debug sessions."""

    def __init__(self, path: Path) -> None:
        self.path = path
        self._memory = InMemoryDiagnosticSink()

    def emit(self, event: DiagnosticEvent) -> None:
        """Append a diagnostic event to JSONL and memory."""

        self.path.parent.mkdir(parents=True, exist_ok=True)
        with self.path.open("a", encoding="utf-8") as handle:
            handle.write(json.dumps(event.to_dict(), sort_keys=True) + "\n")
        self._memory.emit(event)

    def query(self, filters: dict[str, Any]) -> tuple[DiagnosticEvent, ...]:
        """Return events matching simple equality filters."""

        return self._memory.query(filters)

    def recent(self, limit: int) -> tuple[DiagnosticEvent, ...]:
        """Return the most recent events emitted in this process."""

        return self._memory.recent(limit)

    def events_for_trace(self, trace_id: str) -> tuple[DiagnosticEvent, ...]:
        """Return events that mention a trace id."""

        return self._memory.events_for_trace(trace_id)

    def events_for_item(self, item_id: str) -> tuple[DiagnosticEvent, ...]:
        """Return events related to an item or record id."""

        return self._memory.events_for_item(item_id)

    def events_for_artifact(self, path: str) -> tuple[DiagnosticEvent, ...]:
        """Return events related to an artifact path."""

        return self._memory.events_for_artifact(path)

    def export_json(self, path: Path) -> Path:
        """Write in-process events to JSON and return the destination."""

        return self._memory.export_json(path)

    def clear(self) -> None:
        """Clear runtime memory without deleting the JSONL file."""

        self._memory.clear()


class CompositeDiagnosticSink:
    """Fan out diagnostic events to multiple sinks."""

    def __init__(self, sinks: tuple[DiagnosticSink, ...]) -> None:
        self._sinks = sinks

    def emit(self, event: DiagnosticEvent) -> None:
        """Emit one event to every sink."""

        for sink in self._sinks:
            sink.emit(event)

    def query(self, filters: dict[str, Any]) -> tuple[DiagnosticEvent, ...]:
        """Query the first sink that supports stored events."""

        return self._sinks[0].query(filters) if self._sinks else ()

    def recent(self, limit: int) -> tuple[DiagnosticEvent, ...]:
        """Return recent events from the first sink."""

        return self._sinks[0].recent(limit) if self._sinks else ()

    def events_for_trace(self, trace_id: str) -> tuple[DiagnosticEvent, ...]:
        """Return trace events from the first sink."""

        return self._sinks[0].events_for_trace(trace_id) if self._sinks else ()

    def events_for_item(self, item_id: str) -> tuple[DiagnosticEvent, ...]:
        """Return item events from the first sink."""

        return self._sinks[0].events_for_item(item_id) if self._sinks else ()

    def events_for_artifact(self, path: str) -> tuple[DiagnosticEvent, ...]:
        """Return artifact events from the first sink."""

        return self._sinks[0].events_for_artifact(path) if self._sinks else ()

    def export_json(self, path: Path) -> Path:
        """Export events from the first sink."""

        return self._sinks[0].export_json(path)

    def clear(self) -> None:
        """Clear every sink that supports runtime clearing."""

        for sink in self._sinks:
            sink.clear()


ListDiagnosticSink = InMemoryDiagnosticSink


def _matches(event: DiagnosticEvent, filters: dict[str, Any]) -> bool:
    data = event.to_dict()
    return all(data.get(key) == value for key, value in filters.items())
