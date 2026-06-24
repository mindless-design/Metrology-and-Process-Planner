"""Application controller for the modeless setup guide."""

from __future__ import annotations

from dataclasses import dataclass

from metrology_process_planner.domains.session import SessionRecord
from metrology_process_planner.ui.setup_guide import SetupGuidePresenter
from metrology_process_planner.ui.shell import SetupGuideViewModel


@dataclass(frozen=True)
class SetupGuideOpenResult:
    """Result of opening or refreshing the setup guide."""

    status: str
    view_model: SetupGuideViewModel
    message: str = ""


class SetupGuideController:
    """Resolve setup guide commands without owning workflow state."""

    def __init__(self, presenter: SetupGuidePresenter | None = None) -> None:
        self._presenter = presenter if presenter is not None else SetupGuidePresenter()
        self.active_session: SessionRecord | None = None

    def set_active_session(self, session: SessionRecord | None) -> None:
        """Set the session inspected by the guide."""

        self.active_session = session

    def open_current(self) -> SetupGuideOpenResult:
        """Return a modeless setup-guide view model for the active session."""

        view_model = self._presenter.build(self.active_session)
        status = "opened" if self.active_session is not None else "unavailable"
        return SetupGuideOpenResult(status, view_model)
