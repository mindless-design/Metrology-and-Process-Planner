"""Application-level Advanced Diagnostics controller."""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
from pathlib import Path
from typing import Optional

from metrology_process_planner.app.diagnostics_actions import diagnostics_actions
from metrology_process_planner.app.diagnostics_summary import (
    diagnostics_summary_rows,
    missing_artifact_count,
)
from metrology_process_planner.app.diagnostics_windows import open_windows_summary
from metrology_process_planner.app.window_registry import (
    WindowOpenStatus,
    WindowRegistry,
)
from metrology_process_planner.domains.session import (
    ModeRegistry,
    SessionRecord,
    built_in_mode_registry,
)
from metrology_process_planner.infrastructure.diagnostics import (
    DiagnosticSink,
    DiagnosticsService,
)
from metrology_process_planner.persistence.paths import SessionPaths
from metrology_process_planner.ui.diagnostics import (
    DiagnosticsShell,
    InMemoryDiagnosticsWidgetFactory,
)
from metrology_process_planner.ui.shell.view_models import EditorActionViewModel
from metrology_process_planner.workflows.editor.document import SessionDocument


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
    actions: tuple[EditorActionViewModel, ...] = ()


class AdvancedDiagnosticsController:
    """Non-invasive controller for advanced diagnostics actions."""

    def __init__(
        self,
        sink: DiagnosticSink,
        service: DiagnosticsService,
        shell: DiagnosticsShell | None = None,
        mode_registry: ModeRegistry | None = None,
        window_registry: WindowRegistry[object] | None = None,
        editor_document_provider: Callable[[], SessionDocument | None] | None = None,
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
        self._editor_document_provider = editor_document_provider

    def set_active_session(
        self,
        session: SessionRecord,
        paths: Optional[SessionPaths] = None,
    ) -> None:
        """Set the session inspected by diagnostics."""

        self.active_session = session
        self.active_paths = paths

    def set_editor_document_provider(
        self,
        provider: Callable[[], SessionDocument | None] | None,
    ) -> None:
        """Set the current editor document provider inspected by diagnostics."""

        self._editor_document_provider = provider

    def open_current(self) -> DiagnosticsOpenResult:
        """Return the current diagnostics summary for an advanced UI shell."""

        if self.active_session is None:
            return DiagnosticsOpenResult("unavailable", "No active session is loaded.")
        recent_events = self._sink.recent(100)
        summary_rows = diagnostics_summary_rows(
            self.active_session,
            recent_events,
            self._mode_registry,
            self._window_registry,
            self._current_editor_document(),
        )
        result = DiagnosticsOpenResult(
            status="opened",
            message="Advanced diagnostics resolved.",
            warning_count=len(self.active_session.warnings),
            missing_artifact_count=missing_artifact_count(self.active_session),
            recent_event_count=len(recent_events),
            summary_rows=summary_rows,
            actions=diagnostics_actions(self.active_paths, recent_events),
        )
        registry_result = self._window_registry.get_or_create_diagnostics_panel(
            self.active_session.id,
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
            result.actions,
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

    def _current_editor_document(self) -> SessionDocument | None:
        if self._editor_document_provider is None:
            return None
        return self._editor_document_provider()

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
            result.actions,
        )
