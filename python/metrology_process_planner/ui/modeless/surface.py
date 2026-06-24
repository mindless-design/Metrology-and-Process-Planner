"""Small generic modeless shell for view-model-only surfaces."""

from __future__ import annotations

from typing import Any, Protocol


class ModelessSurfaceFactory(Protocol):
    """Backend contract for simple modeless view-model windows."""

    def create_window(self, title: str, view_model: object) -> Any:
        """Create a top-level modeless window."""

    def render(self, window: Any, view_model: object) -> None:
        """Render a view model into an existing window."""

    def show(self, window: Any) -> None:
        """Show a top-level modeless window."""


class ModelessSurfaceShell:
    """Render one view-model surface using an injected backend."""

    def __init__(self, factory: ModelessSurfaceFactory) -> None:
        self._factory = factory

    def open(self, title: str, view_model: object) -> Any:
        """Create, render, and show a modeless view-model window."""

        window = self._factory.create_window(title, view_model)
        self._factory.show(window)
        return window

    def render(self, window: Any, view_model: object) -> None:
        """Refresh an existing modeless view-model window."""

        self._factory.render(window, view_model)


class InMemoryModelessSurfaceFactory:
    """In-memory modeless surface backend for tests and pure smoke checks."""

    def create_window(self, title: str, view_model: object) -> dict[str, Any]:
        """Create an in-memory modeless window record."""

        return {
            "title": title,
            "view_model": view_model,
            "shown": False,
            "resizable": True,
            "scrollable": True,
            "minimum_size": (640, 480),
            "fits_1366x768": True,
        }

    def render(self, window: dict[str, Any], view_model: object) -> None:
        """Store the latest view model on an in-memory window."""

        window["view_model"] = view_model
        window["render_count"] = int(window.get("render_count", 0)) + 1

    def show(self, window: dict[str, Any]) -> None:
        """Mark an in-memory window as shown."""

        window["shown"] = True
