"""Application controller for the modeless setup guide."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from metrology_process_planner.app.commands import CommandId, command_id_from_view_action
from metrology_process_planner.app.window_registry import (
    WindowOpenStatus,
    WindowRegistry,
    surface_key,
)
from metrology_process_planner.domains.session import SessionRecord
from metrology_process_planner.ui.modeless import (
    InMemoryModelessSurfaceFactory,
    ModelessSurfaceShell,
)
from metrology_process_planner.ui.setup_guide import SetupGuidePresenter
from metrology_process_planner.ui.shell import (
    CommandRouter,
    CommandRouteResult,
    SetupGuideViewModel,
)


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
        command_router: CommandRouter | None = None,
    ) -> None:
        self._presenter = presenter if presenter is not None else SetupGuidePresenter()
        self._shell = shell or ModelessSurfaceShell(InMemoryModelessSurfaceFactory())
        self._window_registry = window_registry if window_registry is not None else WindowRegistry()
        self._command_router = command_router
        self.active_session: SessionRecord | None = None
        self.last_action_result: CommandRouteResult | None = None
        self.current_window: Any | None = None

    def set_active_session(self, session: SessionRecord | None) -> None:
        """Set the session inspected by the guide."""

        self.active_session = session

    def set_command_router(self, command_router: CommandRouter | None) -> None:
        """Set the command router used by modeless setup actions."""

        self._command_router = command_router

    def open_current(self) -> SetupGuideOpenResult:
        """Return a modeless setup-guide view model for the active session."""

        view_model = self._presenter.build(self.active_session)
        registry_result = self._window_registry.get_or_create_setup_guide(
            _session_id(self.active_session),
            _window_title(view_model),
            lambda: self._shell.open(_window_title(view_model), view_model),
            refresh_existing=lambda window: self._shell.render(window, view_model),
        )
        if registry_result.status is WindowOpenStatus.FAILED:
            return SetupGuideOpenResult("failed", view_model, registry_result.message)
        if registry_result.window is not None:
            self._attach_action_callback(registry_result.window)
            self.current_window = registry_result.window
        status = _status(registry_result.status, self.active_session)
        return SetupGuideOpenResult(status, view_model, window=registry_result.window)

    def close_current(self) -> None:
        """Close the modeless setup guide for the active session."""

        self._window_registry.close(_window_key(self.active_session))
        self.current_window = None

    def _attach_action_callback(self, window: Any) -> None:
        if isinstance(window, dict):
            window["on_action"] = self.route_action

    def route_action(self, action_id: str) -> CommandRouteResult:
        """Route one setup guide action through the app command router."""

        try:
            command_id = command_id_from_view_action(action_id)
        except ValueError:
            result = CommandRouteResult(
                CommandId.OPEN_SETUP_GUIDE,
                "unavailable",
                f"Unknown setup guide action: {action_id}",
            )
            self.last_action_result = result
            self._render_current()
            return result
        if self._command_router is None:
            result = CommandRouteResult(
                command_id,
                "unavailable",
                "Setup guide command routing is not configured.",
            )
        else:
            result = self._command_router.route(command_id)
        self.last_action_result = result
        self._render_current()
        return result

    def _render_current(self) -> None:
        if self.current_window is None:
            return
        view_model = self._presenter.build(self.active_session)
        self._shell.render(self.current_window, view_model)
        self._attach_action_callback(self.current_window)


def _window_key(session: SessionRecord | None) -> str:
    return surface_key("setup-guide", _session_id(session))


def _session_id(session: SessionRecord | None) -> str:
    return session.id if session is not None else "no-session"


def _window_title(view_model: SetupGuideViewModel) -> str:
    return f"Setup Guide - {view_model.session_name}"


def _status(status: WindowOpenStatus, session: SessionRecord | None) -> str:
    if status is WindowOpenStatus.RAISED:
        return "raised"
    return "opened" if session is not None else "unavailable"
