"""Modeless Reporting Workbench shell with injectable widget backend."""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
from typing import Any, Protocol

from metrology_process_planner.ui.reporting_workbench.view_models import ReportingWorkbenchModel

ActionCallback = Callable[[str], None]
SectionCallback = Callable[[str], None]
TemplateCallback = Callable[[str], None]
ThemeCallback = Callable[[str], None]


@dataclass(frozen=True)
class ReportingWorkbenchCallbacks:
    """Callbacks emitted by the Reporting Workbench."""

    on_action: ActionCallback
    on_select_section: SectionCallback
    on_select_template: TemplateCallback
    on_select_theme: ThemeCallback


class ReportingWorkbenchFactory(Protocol):
    """Backend contract for Reporting Workbench widgets."""

    def create_window(self, title: str) -> Any:
        """Create a top-level workbench window."""

    def render(
        self,
        window: Any,
        model: ReportingWorkbenchModel,
        callbacks: ReportingWorkbenchCallbacks,
    ) -> None:
        """Render the workbench model."""

    def show(self, window: Any) -> None:
        """Show the workbench window."""


class ReportingWorkbenchShell:
    """Render a Reporting Workbench using an injected backend."""

    def __init__(self, factory: ReportingWorkbenchFactory) -> None:
        self._factory = factory

    def open(
        self,
        model: ReportingWorkbenchModel,
        callbacks: ReportingWorkbenchCallbacks,
    ) -> Any:
        """Create, render, and show the modeless workbench."""

        window = self._factory.create_window(model.title)
        self.render(window, model, callbacks)
        self._factory.show(window)
        return window

    def render(
        self,
        window: Any,
        model: ReportingWorkbenchModel,
        callbacks: ReportingWorkbenchCallbacks,
    ) -> None:
        """Render into an existing workbench window."""

        self._factory.render(window, model, callbacks)


class InMemoryReportingWorkbenchFactory:
    """In-memory workbench backend for tests and KLayout-free smoke checks."""

    def create_window(self, title: str) -> dict[str, Any]:
        """Create an in-memory window record."""

        return {"title": title, "shown": False}

    def render(
        self,
        window: dict[str, Any],
        model: ReportingWorkbenchModel,
        callbacks: ReportingWorkbenchCallbacks,
    ) -> None:
        """Store the rendered workbench model and callbacks."""

        window["model"] = model
        window["header"] = model.header
        window["sections"] = model.sections
        window["preview"] = model.preview
        window["inspector"] = model.inspector
        window["actions"] = model.actions
        window["on_action"] = callbacks.on_action
        window["on_select_section"] = callbacks.on_select_section
        window["on_select_template"] = callbacks.on_select_template
        window["on_select_theme"] = callbacks.on_select_theme

    def show(self, window: dict[str, Any]) -> None:
        """Mark the in-memory window as shown."""

        window["shown"] = True
