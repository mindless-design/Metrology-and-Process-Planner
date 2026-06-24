"""Application controller for the modeless setup guide."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from metrology_process_planner.app.window_registry import WindowOpenStatus, WindowRegistry
from metrology_process_planner.domains.session import SessionRecord
from metrology_process_planner.ui.modeless import (
    InMemoryModelessSurfaceFactory,
    ModelessSurfaceShell,
)
from metrology_process_planner.ui.setup_guide import SetupGuidePresenter
from metrology_process_planner.ui.shell import SetupGuideViewModel


@dataclass(frozen=True)
class SetupGuideOpenResult:
    """Result of opening or refreshing the setup guide."""

    status: str
    view_model: SetupGuideViewModel
    message: str = ""
    window: Any | None = None


class SetupGuideController:
    """Resolve setup guide commands without owning workflow state."""

    def __init__(
        self,
        presenter: SetupGuidePresenter | None = None,
        shell: ModelessSurfaceShell | None = None,
        window_registry: WindowRegistry[Any] | None = None,
    ) -> None:
        self._presenter = presenter if presenter is not None else SetupGuidePresenter()
        self._shell = shell or ModelessSurfaceShell(InMemoryModelessSurfaceFactory())
        self._window_registry = window_registry if window_registry is not None else WindowRegistry()
        self.active_session: SessionRecord | None = None

    def set_active_session(self, session: SessionRecord | None) -> None:
        """Set the session inspected by the guide."""

        self.active_session = session

    def open_current(self) -> SetupGuideOpenResult:
        """Return a modeless setup-guide view model for the active session."""

        view_model = self._presenter.build(self.active_session)
        registry_result = self._window_registry.open_or_raise(
            _window_key(self.active_session),
            _window_title(view_model),
            lambda: self._shell.open(_window_title(view_model), view_model),
            refresh_existing=lambda window: self._shell.render(window, view_model),
        )
        if registry_result.status is WindowOpenStatus.FAILED:
            return SetupGuideOpenResult("failed", view_model, registry_result.message)
        status = _status(registry_result.status, self.active_session)
        return SetupGuideOpenResult(status, view_model, window=registry_result.window)


def _window_key(session: SessionRecord | None) -> str:
    session_id = session.id if session is not None else "no-session"
    return f"setup-guide:{session_id}"


def _window_title(view_model: SetupGuideViewModel) -> str:
    return f"Setup Guide - {view_model.session_name}"


def _status(status: WindowOpenStatus, session: SessionRecord | None) -> str:
    if status is WindowOpenStatus.RAISED:
        return "raised"
    return "opened" if session is not None else "unavailable"
