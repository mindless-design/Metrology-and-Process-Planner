"""Application controller for the modeless Reporting Workbench."""

from __future__ import annotations

from dataclasses import replace
from typing import Any, Protocol

from metrology_process_planner.app.commands import CommandId
from metrology_process_planner.app.report_output_adapter import (
    ReportOutputAdapter,
    UnavailableReportOutputAdapter,
)
from metrology_process_planner.app.reporting_workbench_actions import dispatch_workbench_action
from metrology_process_planner.app.reporting_workbench_defaults import default_report_request
from metrology_process_planner.app.reporting_workbench_output import choose_report_output_dir
from metrology_process_planner.app.window_registry import WindowOpenStatus, WindowRegistry
from metrology_process_planner.domains.session import ModeRegistry, SessionRecord
from metrology_process_planner.persistence.paths import SessionPaths
from metrology_process_planner.reporting import ReportGenerationService, ReportRequest
from metrology_process_planner.reporting.templates import built_in_report_templates
from metrology_process_planner.reporting.themes import built_in_report_themes
from metrology_process_planner.ui.reporting_workbench import (
    InMemoryReportingWorkbenchFactory,
    ReportingWorkbenchCallbacks,
    ReportingWorkbenchModel,
    ReportingWorkbenchShell,
)
from metrology_process_planner.ui.reporting_workbench.presenter import ReportingWorkbenchPresenter
from metrology_process_planner.ui.shell import CommandRouteResult
from metrology_process_planner.workflows.editor.document import SessionDocument


class ReportingArtifactRepairService(Protocol):
    """Repair service boundary used by the Reporting Workbench."""

    def regenerate_missing(
        self,
        document: SessionDocument,
        paths: SessionPaths,
    ) -> SessionDocument:
        """Return a refreshed document after regenerating missing artifacts."""

    def regenerate_stale(
        self,
        document: SessionDocument,
        paths: SessionPaths,
    ) -> SessionDocument:
        """Return a refreshed document after regenerating stale artifacts."""


class ReportingWorkbenchController:
    """Open, refresh, and dispatch the modeless Reporting Workbench."""

    def __init__(
        self,
        window_registry: WindowRegistry[Any] | None = None,
        shell: ReportingWorkbenchShell | None = None,
        generation_service: ReportGenerationService | None = None,
        artifact_repair_service: ReportingArtifactRepairService | None = None,
        output_adapter: ReportOutputAdapter | None = None,
        active_session_updater: Any | None = None,
        mode_registry: ModeRegistry | None = None,
    ) -> None:
        self._window_registry = window_registry if window_registry is not None else WindowRegistry()
        self._shell = shell if shell is not None else _default_shell()
        self._presenter = ReportingWorkbenchPresenter(mode_registry=mode_registry)
        self._generation_service = generation_service or ReportGenerationService(
            mode_registry=mode_registry,
        )
        self._mode_registry = mode_registry
        self._artifact_repair_service = artifact_repair_service
        self._output_adapter = output_adapter or UnavailableReportOutputAdapter()
        self._active_session_updater = active_session_updater
        self.current_document: SessionDocument | None = None
        self.current_paths: SessionPaths | None = None
        self.current_request: ReportRequest | None = None
        self.current_window: Any | None = None
        self.last_result: CommandRouteResult | None = None
        self._selected_section_id = ""
        self._callbacks: ReportingWorkbenchCallbacks | None = None
    @property
    def artifact_repair_service(self) -> ReportingArtifactRepairService | None:
        """Return the optional artifact repair service for workbench actions."""

        return self._artifact_repair_service
    @property
    def window_registry(self) -> WindowRegistry[Any]:
        """Return the shared modeless window registry."""

        return self._window_registry
    @property
    def output_adapter(self) -> ReportOutputAdapter:
        """Return the report output adapter for action helpers."""

        return self._output_adapter

    def default_request(self) -> ReportRequest:
        """Return the default report request for the active workbench document."""

        if self.current_document is None or self.current_paths is None:
            raise RuntimeError("Reporting Workbench has no active document.")
        return _default_request(self.current_document, self.current_paths)

    def open_document(
        self,
        document: SessionDocument,
        paths: SessionPaths,
    ) -> CommandRouteResult:
        """Open or raise the workbench for a session document."""

        self.current_document = document
        self.current_paths = paths
        if self.current_request is None or self.current_request.session_id != document.session.id:
            self.current_request = _default_request(document, paths)
        callbacks = _callbacks_for(self)
        self._callbacks = callbacks
        model = self._model()
        result = self._window_registry.open_or_raise(
            _workbench_key(document.session.id),
            model.title,
            lambda: self._shell.open(model, callbacks),
            refresh_existing=lambda window: self._shell.render(window, self._model(), callbacks),
        )
        if result.status is WindowOpenStatus.FAILED:
            return CommandRouteResult(CommandId.OPEN_REPORTING_WORKBENCH, "failed", result.message)
        self.current_window = result.window
        return CommandRouteResult(
            CommandId.OPEN_REPORTING_WORKBENCH,
            "success",
            "Reporting Workbench opened.",
        )

    def dispatch(self, action_id: str) -> CommandRouteResult:
        """Dispatch a workbench action."""

        result = dispatch_workbench_action(self, action_id)
        self.last_result = result
        self._render_current()
        return result

    def replace_after_export(self, session: SessionRecord) -> None:
        """Refresh workbench and active editor state after export registration."""

        from metrology_process_planner.workflows.editor.builder import SessionDocumentBuilder

        self.current_document = SessionDocumentBuilder(
            mode_registry=self._mode_registry,
        ).build(session)
        if self._active_session_updater is not None:
            self._active_session_updater(session)

    def select_section(self, section_id: str) -> None:
        """Select a section in the workbench preview."""

        self._selected_section_id = section_id
        self._render_current()

    def select_template(self, template_id: str) -> None:
        """Select a different report template."""

        if self.current_request is not None and template_id in built_in_report_templates():
            self.current_request = replace(self.current_request, template_id=template_id)
        self._render_current()

    def select_theme(self, theme_id: str) -> None:
        """Select a different report output theme."""

        if self.current_request is not None and theme_id in built_in_report_themes():
            self.current_request = replace(self.current_request, theme_id=theme_id)
        self._render_current()

    def choose_output_dir(self) -> CommandRouteResult:
        """Select and persist a report output folder on the current request."""

        return choose_report_output_dir(self)

    def _model(self) -> ReportingWorkbenchModel:
        if self.current_document is None or self.current_request is None:
            raise RuntimeError("Reporting Workbench has no active document.")
        return self._presenter.build(
            self.current_document,
            self.current_request,
            self._selected_section_id,
            self.last_result,
        )

    def _render_current(self) -> None:
        if self.current_window is not None and self._callbacks is not None:
            self._shell.render(self.current_window, self._model(), self._callbacks)


def _default_shell() -> ReportingWorkbenchShell:
    return ReportingWorkbenchShell(InMemoryReportingWorkbenchFactory())


def _callbacks_for(controller: ReportingWorkbenchController) -> ReportingWorkbenchCallbacks:
    def dispatch(action_id: str) -> None:
        """Dispatch dispatch."""
        controller.dispatch(action_id)

    return ReportingWorkbenchCallbacks(
        dispatch,
        controller.select_section,
        controller.select_template,
        controller.select_theme,
    )


def _default_request(document: SessionDocument, paths: SessionPaths) -> ReportRequest:
    return default_report_request(document, paths)


def _workbench_key(session_id: str) -> str:
    return f"reporting_workbench:{session_id}"
