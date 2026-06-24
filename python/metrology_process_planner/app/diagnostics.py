"""Application-level Advanced Diagnostics controller."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Optional

from metrology_process_planner.app.diagnostics_windows import open_windows_summary
from metrology_process_planner.app.window_registry import (
    WindowOpenStatus,
    WindowRegistry,
)
from metrology_process_planner.domains.session import (
    ArtifactStatus,
    ModeRegistry,
    SessionRecord,
    built_in_mode_registry,
)
from metrology_process_planner.infrastructure.diagnostics import (
    DiagnosticEvent,
    DiagnosticSink,
    DiagnosticsService,
)
from metrology_process_planner.persistence.paths import SessionPaths
from metrology_process_planner.ui.diagnostics import (
    DiagnosticsShell,
    InMemoryDiagnosticsWidgetFactory,
)


@dataclass(frozen=True)
class DiagnosticsOpenResult:
    """Result of opening or resolving the diagnostics surface."""

    status: str
    message: str = ""
    warning_count: int = 0
    missing_artifact_count: int = 0
    recent_event_count: int = 0
    window: object | None = None
    summary_rows: tuple[tuple[str, str], ...] = ()


class AdvancedDiagnosticsController:
    """Non-invasive controller for advanced diagnostics actions."""

    def __init__(
        self,
        sink: DiagnosticSink,
        service: DiagnosticsService,
        shell: DiagnosticsShell | None = None,
        mode_registry: ModeRegistry | None = None,
        window_registry: WindowRegistry[object] | None = None,
    ) -> None:
        self._sink = sink
        self._service = service
        self._shell = shell if shell is not None else DiagnosticsShell(
            InMemoryDiagnosticsWidgetFactory()
        )
        self._mode_registry = mode_registry or built_in_mode_registry()
        self._window_registry = (
            window_registry if window_registry is not None else WindowRegistry(diagnostic_sink=sink)
        )
        self.active_session: Optional[SessionRecord] = None
        self.active_paths: Optional[SessionPaths] = None

    def set_active_session(
        self,
        session: SessionRecord,
        paths: Optional[SessionPaths] = None,
    ) -> None:
        """Set the session inspected by diagnostics."""

        self.active_session = session
        self.active_paths = paths

    def open_current(self) -> DiagnosticsOpenResult:
        """Return the current diagnostics summary for an advanced UI shell."""

        if self.active_session is None:
            return DiagnosticsOpenResult("unavailable", "No active session is loaded.")
        recent_events = self._sink.recent(100)
        summary_rows = _summary_rows(
            self.active_session,
            recent_events,
            self._mode_registry,
            self._window_registry,
        )
        result = DiagnosticsOpenResult(
            status="opened",
            message="Advanced diagnostics resolved.",
            warning_count=len(self.active_session.warnings),
            missing_artifact_count=_missing_artifact_count(self.active_session),
            recent_event_count=len(recent_events),
            summary_rows=summary_rows,
        )
        registry_result = self._window_registry.open_or_raise(
            _diagnostics_window_key(self.active_session),
            "Advanced Diagnostics",
            lambda: self._shell.open(result, recent_events),
            refresh_existing=lambda window: self._shell.render(
                window,
                result,
                recent_events,
            ),
        )
        if registry_result.status is WindowOpenStatus.FAILED:
            return DiagnosticsOpenResult("failed", registry_result.message)
        if registry_result.window is not None:
            result = _with_open_window_rows(result, open_windows_summary(self._window_registry))
            self._shell.render(registry_result.window, result, recent_events)
        return DiagnosticsOpenResult(
            "raised" if registry_result.status is WindowOpenStatus.RAISED else result.status,
            result.message,
            result.warning_count,
            result.missing_artifact_count,
            result.recent_event_count,
            registry_result.window,
            result.summary_rows,
        )

    def export_debug_bundle(self, output_path: Path) -> Path:
        """Export a debug bundle for the active session."""

        if self.active_session is None:
            raise RuntimeError("No active session is loaded.")
        return self._service.export_debug_bundle(
            self.active_session,
            output_path,
            self.active_paths,
        )


def _summary_rows(
    session: SessionRecord,
    recent_events: tuple[DiagnosticEvent, ...],
    mode_registry: ModeRegistry,
    window_registry: WindowRegistry[object] | None = None,
) -> tuple[tuple[str, str], ...]:
    return (
        ("Status", "opened"),
        ("Message", "Advanced diagnostics resolved."),
        ("Session", f"{session.name} ({session.id})"),
        ("Mode", session.mode.value),
        ("Loaded Modes", _loaded_modes(session, mode_registry)),
        ("Artifacts", _artifact_summary(session)),
        ("Warnings", str(len(session.warnings))),
        ("Warning Codes", _warning_codes(session)),
        ("Missing Artifacts", str(_missing_artifact_count(session))),
        ("Recent Commands", _recent_commands(recent_events)),
        ("Recent Events", _recent_event_names(recent_events)),
        ("Recent Event Count", str(len(recent_events))),
        ("Open Windows", open_windows_summary(window_registry)),
    )


def _loaded_modes(session: SessionRecord, mode_registry: ModeRegistry) -> str:
    requested = dict(session.extensions or {}).get("mode_validation", {})
    requested_mode = requested.get("requested_mode") if isinstance(requested, dict) else None
    modes = list(mode_registry.mode_ids())
    if requested_mode and requested_mode not in modes:
        modes.append(str(requested_mode))
    return ", ".join(modes)


def _artifact_summary(session: SessionRecord) -> str:
    artifacts = tuple((session.artifacts or {}).values())
    if not artifacts:
        return "0 total"
    counts: dict[str, int] = {}
    for artifact in artifacts:
        counts[artifact.status.value] = counts.get(artifact.status.value, 0) + 1
    status_text = "; ".join(f"{key}={counts[key]}" for key in sorted(counts))
    return f"{len(artifacts)} total; {status_text}"


def _missing_artifact_count(session: SessionRecord) -> int:
    return sum(
        1
        for artifact in (session.artifacts or {}).values()
        if artifact.status is ArtifactStatus.MISSING
    )


def _warning_codes(session: SessionRecord) -> str:
    codes = sorted({warning.code for warning in session.warnings if warning.code})
    return ", ".join(codes) if codes else "none"


def _recent_commands(events: tuple[DiagnosticEvent, ...]) -> str:
    commands = [event.operation for event in events if event.category == "command"]
    return ", ".join(commands[-5:]) if commands else "none"


def _recent_event_names(events: tuple[DiagnosticEvent, ...]) -> str:
    return ", ".join(event.event_name for event in events[-5:]) if events else "none"


def _diagnostics_window_key(session: SessionRecord) -> str:
    return f"advanced-diagnostics:{session.id}"


def _with_open_window_rows(
    result: DiagnosticsOpenResult,
    open_windows: str,
) -> DiagnosticsOpenResult:
    rows = tuple(
        (key, open_windows) if key == "Open Windows" else (key, value)
        for key, value in result.summary_rows
    )
    return DiagnosticsOpenResult(
        result.status,
        result.message,
        result.warning_count,
        result.missing_artifact_count,
        result.recent_event_count,
        result.window,
        rows,
    )
