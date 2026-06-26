"""Structured diagnostics models for seam tracing."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Optional
from uuid import uuid4

from metrology_process_planner import __version__


@dataclass(frozen=True)
class DiagnosticEvent:
    """A JSON-serializable event emitted when objects cross workflow seams."""

    message: str
    severity: str = "info"
    source: str = "core"
    event_name: str = "DiagnosticEvent"
    category: str = "workflow"
    operation: str = ""
    session_id: str = ""
    trace_ids: dict[str, str] = field(default_factory=dict)
    event_id: str = field(default_factory=lambda: f"evt_{uuid4().hex}")
    timestamp: str = field(default_factory=lambda: _utc_now_iso())
    before_state_summary: Optional[dict[str, Any]] = None
    after_state_summary: Optional[dict[str, Any]] = None
    expected: Optional[Any] = None
    actual: Optional[Any] = None
    related_record_ids: tuple[str, ...] = ()
    related_artifact_paths: tuple[str, ...] = ()
    exception_type: str = ""
    exception_message: str = ""
    stack_trace: str = ""
    user_visible_warning_id: str = ""
    remediation_hint: str = ""

    @property
    def source_component(self) -> str:
        """Return the emitting component name."""

        return self.source

    def to_dict(self) -> dict[str, Any]:
        """Serialize the event to JSON-compatible structured data."""

        return {
            "event_id": self.event_id,
            "timestamp": self.timestamp,
            "severity": self.severity,
            "category": self.category,
            "event_name": self.event_name,
            "message": self.message,
            "session_id": self.session_id,
            "trace_ids": dict(self.trace_ids),
            "source_component": self.source_component,
            "operation": self.operation,
            "before_state_summary": self.before_state_summary,
            "after_state_summary": self.after_state_summary,
            "expected": self.expected,
            "actual": self.actual,
            "related_record_ids": list(self.related_record_ids),
            "related_artifact_paths": list(self.related_artifact_paths),
            "exception_type": self.exception_type,
            "exception_message": self.exception_message,
            "stack_trace": self.stack_trace,
            "user_visible_warning_id": self.user_visible_warning_id,
            "remediation_hint": self.remediation_hint,
        }


@dataclass(frozen=True)
class DiagnosticsSnapshot:
    """A portable diagnostics report for support and UI display."""

    plugin_version: str
    package_root: str
    python_root: str
    events: tuple[DiagnosticEvent, ...] = ()

    def to_dict(self) -> dict[str, object]:
        """Serialize the snapshot to JSON-compatible data."""

        return {
            "plugin_version": self.plugin_version,
            "package_root": self.package_root,
            "python_root": self.python_root,
            "events": [event.to_dict() for event in self.events],
        }

    @classmethod
    def for_root(
        cls,
        package_root: str,
        events: tuple[DiagnosticEvent, ...] = (),
    ) -> DiagnosticsSnapshot:
        """Create a snapshot for a package root."""

        return cls(__version__, package_root, f"{package_root}\\python", events)


@dataclass(frozen=True)
class DiffResult:
    """Compact comparison result for a seam or state integrity check."""

    ok: bool
    missing: tuple[str, ...] = ()
    extra: tuple[str, ...] = ()
    mismatched: tuple[str, ...] = ()
    warnings: tuple[str, ...] = ()
    suggested_repairs: tuple[str, ...] = ()

    def to_dict(self) -> dict[str, object]:
        """Serialize the diff result to JSON-compatible data."""

        return {
            "ok": self.ok,
            "missing": list(self.missing),
            "extra": list(self.extra),
            "mismatched": list(self.mismatched),
            "warnings": list(self.warnings),
            "suggested_repairs": list(self.suggested_repairs),
        }


def _utc_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds").replace("+00:00", "Z")
