"""Application-level Advanced Diagnostics controller."""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
from pathlib import Path
from typing import cast

from metrology_process_planner.app.diagnostics_action_dispatch import (
    DiagnosticsActionContext,
    DiagnosticsActionDispatcher,
)
from metrology_process_planner.app.diagnostics_action_results import DiagnosticsActionResult
from metrology_process_planner.app.diagnostics_actions import diagnostics_actions
from metrology_process_planner.app.diagnostics_dashboard_rows import (
    with_dashboard_context_rows,
)
from metrology_process_planner.app.diagnostics_summary import (
    diagnostics_summary_rows,
    missing_artifact_count,
)
from metrology_process_planner.app.diagnostics_window_open import (
    open_or_refresh_diagnostics_window,
)
from metrology_process_planner.app.window_registry import WindowRegistry
from metrology_process_planner.diagnostics import (
    DiagnosticEvent,
    DiagnosticSink,
    DiagnosticsService,
)
from metrology_process_planner.domains.session import (
    ModeRegistry,
    SessionRecord,
    built_in_mode_registry,
)
from metrology_process_planner.domains.warnings.warning_visibility import (
    warning_visible_for_session,
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
        mode_load_warnings: tuple[str, ...] = (),
        window_registry: WindowRegistry[object] | None = None,
        editor_document_provider: Callable[[], SessionDocument | None] | None = None,
    ) -> None:
        self._sink = sink
        self._service = service
        self._shell = shell if shell is not None else DiagnosticsShell(
            InMemoryDiagnosticsWidgetFactory()
        )
        self._mode_registry = mode_registry or built_in_mode_registry()
        self._mode_load_warnings = mode_load_warnings
        self._window_registry = (
            window_registry if window_registry is not None else WindowRegistry(diagnostic_sink=sink)
        )
        self.active_session: SessionRecord | None = None
        self.active_paths: SessionPaths | None = None
        self._editor_document_provider = editor_document_provider
        self._action_dispatcher = DiagnosticsActionDispatcher(sink)
        self.last_action_result: DiagnosticsActionResult | None = None

    def set_active_session(
        self,
        session: SessionRecord,
        paths: SessionPaths | None = None,
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

        session = self.active_session
        if session is None:
            return DiagnosticsOpenResult("unavailable", "No active session is loaded.")
        recent_events = self._sink.recent(100)
        result = self._build_open_result(session, recent_events)
        opened = open_or_refresh_diagnostics_window(self, result, recent_events)
        return cast(DiagnosticsOpenResult, opened)

    def _build_open_result(
        self,
        session: SessionRecord,
        recent_events: tuple[DiagnosticEvent, ...],
    ) -> DiagnosticsOpenResult:
        editor_document = self._current_editor_document()
        summary_rows = diagnostics_summary_rows(
            session,
            recent_events,
            self._mode_registry,
            self._window_registry,
            editor_document,
        )
        summary_rows = with_dashboard_context_rows(
            summary_rows,
            session,
            self.active_paths,
            editor_document,
            self._mode_registry,
        )
        if self._mode_load_warnings:
            summary_rows += (("Mode Load Warnings", "; ".join(self._mode_load_warnings)),)
        return DiagnosticsOpenResult(
            status="opened",
            message="Advanced diagnostics resolved.",
            warning_count=_visible_warning_count(session, self._mode_registry),
            missing_artifact_count=missing_artifact_count(session, self._mode_registry),
            recent_event_count=len(recent_events),
            summary_rows=summary_rows,
            actions=diagnostics_actions(self.active_paths, recent_events),
        )

    def export_debug_bundle(self, output_path: Path) -> Path:
        """Export a debug bundle for the active session."""

        if self.active_session is None:
            raise RuntimeError("No active session is loaded.")
        return cast(
            Path,
            self._service.export_debug_bundle(
                self.active_session,
                output_path,
                self.active_paths,
            ),
        )

    def route_action(self, action_id: str) -> DiagnosticsActionResult:
        """Dispatch an action from the modeless diagnostics shell."""

        if self.active_session is None:
            return DiagnosticsActionResult(action_id, "unavailable", "No active session is loaded.")
        context = DiagnosticsActionContext(
            self.active_session,
            self.active_paths,
            self._sink.recent(100),
            self._mode_registry,
            self._service,
        )
        self.last_action_result = self._action_dispatcher.dispatch(action_id, context)
        self.open_current()
        return self.last_action_result

    def _current_editor_document(self) -> SessionDocument | None:
        if self._editor_document_provider is None:
            return None
        return self._editor_document_provider()


def _visible_warning_count(
    session: SessionRecord,
    mode_registry: ModeRegistry | None = None,
) -> int:
    return sum(
        1
        for warning in session.warnings
        if warning_visible_for_session(session, warning, mode_registry)
    )
