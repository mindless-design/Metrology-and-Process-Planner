"""Minimal Advanced Diagnostics shell with injectable widget backend."""

from __future__ import annotations

from typing import Any, Protocol

from metrology_process_planner.infrastructure.diagnostics import DiagnosticEvent


class DiagnosticsWidgetFactory(Protocol):
    """Backend contract for constructing diagnostics widgets."""

    def create_window(self, title: str) -> Any:
        """Create a top-level diagnostics window."""

    def set_summary(self, window: Any, entries: tuple[tuple[str, str], ...]) -> None:
        """Render active session/workflow summary rows."""

    def set_events(self, window: Any, events: tuple[DiagnosticEvent, ...]) -> None:
        """Render recent diagnostic events."""

    def set_actions(self, window: Any, actions: tuple[str, ...]) -> None:
        """Render advanced diagnostics action labels."""

    def show(self, window: Any) -> None:
        """Show the diagnostics window."""


class DiagnosticsShell:
    """Render the advanced diagnostics surface using an injected backend."""

    def __init__(self, factory: DiagnosticsWidgetFactory) -> None:
        self._factory = factory

    def open(
        self,
        result: Any,
        recent_events: tuple[DiagnosticEvent, ...],
    ) -> Any:
        """Build and show the diagnostics shell."""

        window = self._factory.create_window("Advanced Diagnostics")
        self.render(window, result, recent_events)
        self._factory.show(window)
        return window

    def render(
        self,
        window: Any,
        result: Any,
        recent_events: tuple[DiagnosticEvent, ...],
    ) -> None:
        """Render diagnostics content into an existing shell window."""

        self._factory.set_summary(window, _summary_rows(result))
        self._factory.set_events(window, recent_events)
        self._factory.set_actions(
            window,
            (
                "Run Seam Checks",
                "Export Debug Bundle",
                "Copy Selected Trace",
                "Open Diagnostics Folder",
                "Clear Runtime Events",
            ),
        )


class InMemoryDiagnosticsWidgetFactory:
    """Widget factory used by tests and pure smoke checks."""

    def create_window(self, title: str) -> dict[str, Any]:
        """Create an in-memory diagnostics window."""

        return {"title": title, "shown": False}

    def set_summary(self, window: dict[str, Any], entries: tuple[tuple[str, str], ...]) -> None:
        """Store summary rows."""

        window["summary"] = entries

    def set_events(self, window: dict[str, Any], events: tuple[DiagnosticEvent, ...]) -> None:
        """Store recent event rows."""

        window["events"] = events

    def set_actions(self, window: dict[str, Any], actions: tuple[str, ...]) -> None:
        """Store action labels."""

        window["actions"] = actions

    def show(self, window: dict[str, Any]) -> None:
        """Mark the in-memory window as shown."""

        window["shown"] = True


def _summary_rows(result: Any) -> tuple[tuple[str, str], ...]:
    rows = getattr(result, "summary_rows", ())
    if rows:
        return tuple(rows)
    return (
        ("Status", result.status),
        ("Message", result.message),
        ("Warnings", str(result.warning_count)),
        ("Missing Artifacts", str(result.missing_artifact_count)),
        ("Recent Events", str(result.recent_event_count)),
    )
