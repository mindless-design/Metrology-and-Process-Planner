"""KLayout/Qt modeless shell for setup-guide cards."""

from __future__ import annotations

from typing import Any

from metrology_process_planner.infrastructure.klayout.session_editor_regions import (
    render_text_region,
)
from metrology_process_planner.ui.setup_guide import setup_stage_cards
from metrology_process_planner.ui.shell import SetupGuideViewModel


class KLayoutSetupGuideSurfaceFactory:
    """Render setup-guide stage cards with Qt widgets when available."""

    def __init__(self, pya_module: Any) -> None:
        self._pya = pya_module

    def create_window(self, title: str, view_model: object) -> Any:
        """Create a setup-guide window and render the initial view model."""

        widget_class = getattr(self._pya, "QWidget", None)
        if widget_class is None:
            window = _fallback_window(title)
            self.render(window, view_model)
            return window
        window = widget_class()
        _call(window, "setWindowTitle", title)
        _set_state(window, "title", title)
        _install_layout(self._pya, window)
        self.render(window, view_model)
        return window

    def render(self, window: Any, view_model: object) -> None:
        """Render setup cards into an existing modeless window."""

        if not isinstance(view_model, SetupGuideViewModel):
            _set_state(window, "view_model", view_model)
            return
        cards = setup_stage_cards(view_model)
        _set_state(window, "view_model", view_model)
        _set_state(window, "setup_stage_cards", cards)
        _set_state(window, "setup_status", view_model.status_message)
        _set_state(window, "setup_footer_actions", tuple(view_model.action_views))
        render_text_region(self._pya, window, "setup_header", _header_rows(view_model))
        render_text_region(self._pya, window, "setup_stage_cards", _card_rows(cards))
        render_text_region(self._pya, window, "setup_footer_actions", _action_rows(view_model))

    def show(self, window: Any) -> None:
        """Show the setup-guide window."""

        _set_state(window, "shown", True)
        _call(window, "show")


def _fallback_window(title: str) -> dict[str, Any]:
    return {
        "title": title,
        "shown": False,
        "resizable": True,
        "scrollable": True,
        "minimum_size": (720, 520),
        "fits_1366x768": True,
    }


def _header_rows(view_model: SetupGuideViewModel) -> tuple[str, ...]:
    return (
        view_model.session_name,
        view_model.mode_display_name,
        view_model.status_message,
        view_model.capture_status_message,
    )


def _card_rows(cards: tuple[object, ...]) -> tuple[str, ...]:
    return tuple(_card_text(card) for card in cards)


def _card_text(card: Any) -> str:
    parts = (
        card.title,
        card.status_label,
        card.requirement_label,
        card.artifact_label,
        card.warning_label,
        card.primary_action_label,
    )
    return " | ".join(part for part in parts if part)


def _action_rows(view_model: SetupGuideViewModel) -> tuple[str, ...]:
    return tuple(action.label for action in view_model.action_views)


def _install_layout(pya: Any, window: Any) -> None:
    layout_class = getattr(pya, "QVBoxLayout", None)
    if layout_class is None:
        return
    layout = layout_class()
    _set_state(window, "qt_layout", layout)
    _call(window, "setLayout", layout)


def _set_state(window: Any, key: str, value: Any) -> None:
    if isinstance(window, dict):
        window[key] = value
        return
    state = getattr(window, "_mpp_state", None)
    if state is None:
        state = {}
        try:
            window._mpp_state = state
        except Exception:  # noqa: BLE001 - Qt wrappers may reject dynamic attrs.
            return
    state[key] = value


def _call(target: Any, name: str, *args: Any) -> None:
    method = getattr(target, name, None)
    if callable(method):
        method(*args)
