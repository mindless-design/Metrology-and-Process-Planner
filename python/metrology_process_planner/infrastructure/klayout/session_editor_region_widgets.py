"""Generic Qt widget helpers for KLayout session editor regions."""

from __future__ import annotations

from typing import Any


def region_container(pya: Any) -> Any | None:
    """Return a Qt container widget when KLayout exposes one."""

    widget_class = getattr(pya, "QWidget", None)
    return widget_class() if widget_class is not None else None


def layout(pya: Any, container: Any) -> Any | None:
    """Attach and return a vertical layout for a region container."""

    layout_class = getattr(pya, "QVBoxLayout", None)
    if layout_class is None:
        return None
    region_layout = layout_class()
    call(container, "setLayout", region_layout)
    return region_layout


def label(pya: Any, text: str) -> Any:
    """Return a QLabel when available, otherwise the plain text."""

    label_class = getattr(pya, "QLabel", None)
    return label_class(text) if label_class is not None else text


def button(pya: Any, text: str) -> Any:
    """Return a QPushButton when available, otherwise the plain text."""

    button_class = getattr(pya, "QPushButton", None)
    return button_class(text) if button_class is not None else text


def add_widget(region_layout: Any | None, widget: Any) -> None:
    """Add a child widget when a Qt layout exists."""

    if region_layout is not None:
        call(region_layout, "addWidget", widget)


def attach_region(window: Any, key: str, container: Any) -> None:
    """Remember a rendered region and attach it to the parent layout."""

    state = qt_state(window)
    state.setdefault("qt_regions", {})[key] = container
    region_layout = state.get("qt_layout")
    if region_layout is not None:
        add_widget(region_layout, container)


def call(target: Any, name: str, *args: Any) -> None:
    """Call a Qt wrapper method when it is available."""

    method = getattr(target, name, None)
    if callable(method):
        method(*args)


def qt_state(window: Any) -> dict[str, Any]:
    """Return the mutable state dictionary attached to a Qt wrapper."""

    state = getattr(window, "_mpp_state", None)
    if state is None:
        state = {}
        try:
            window._mpp_state = state
        except Exception:  # noqa: BLE001 - Qt wrappers may reject dynamic attrs.
            return {}
    return state
