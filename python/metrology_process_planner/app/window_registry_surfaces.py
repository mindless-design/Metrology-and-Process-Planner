"""Named product-surface helpers for modeless window registries."""

from __future__ import annotations

from collections.abc import Callable
from typing import Generic, Protocol, TypeVar, cast

from metrology_process_planner.app.window_registry_types import WindowOpenResult

WindowT = TypeVar("WindowT")


class _RegistryLifecycle(Protocol[WindowT]):
    def open_or_raise(
        self,
        key: str,
        title: str,
        create: Callable[[], WindowT],
        *,
        refresh_existing: Callable[[WindowT], None] | None = None,
    ) -> WindowOpenResult[WindowT]:
        """Create or raise a window for one logical key."""


class WindowSurfaceMixin(Generic[WindowT]):
    """Named modeless product-surface entrypoints."""

    def get_or_create_session_editor(
        self,
        session_id: str,
        title: str,
        create: Callable[[], WindowT],
        *,
        refresh_existing: Callable[[WindowT], None] | None = None,
    ) -> WindowOpenResult[WindowT]:
        """Create or raise the modeless session editor for one session."""

        return _open_surface(
            self,
            "session-editor",
            session_id,
            title,
            create,
            refresh_existing,
        )

    def get_or_create_setup_guide(
        self,
        session_id: str,
        title: str,
        create: Callable[[], WindowT],
        *,
        refresh_existing: Callable[[WindowT], None] | None = None,
    ) -> WindowOpenResult[WindowT]:
        """Create or raise the modeless setup guide for one session."""

        return _open_surface(
            self,
            "setup-guide",
            session_id,
            title,
            create,
            refresh_existing,
        )

    def get_or_create_recipe_editor(
        self,
        recipe_id: str,
        title: str,
        create: Callable[[], WindowT],
        *,
        refresh_existing: Callable[[WindowT], None] | None = None,
    ) -> WindowOpenResult[WindowT]:
        """Create or raise the modeless recipe editor for one recipe."""

        return _open_surface(
            self,
            "recipe-editor",
            recipe_id,
            title,
            create,
            refresh_existing,
        )

    def get_or_create_diagnostics_panel(
        self,
        session_id: str,
        title: str,
        create: Callable[[], WindowT],
        *,
        refresh_existing: Callable[[WindowT], None] | None = None,
    ) -> WindowOpenResult[WindowT]:
        """Create or raise the modeless diagnostics panel for one session."""

        return _open_surface(
            self,
            "advanced-diagnostics",
            session_id,
            title,
            create,
            refresh_existing,
        )


def surface_key(surface_id: str, owner_id: str) -> str:
    """Return a stable modeless surface key for diagnostics and tests."""

    return f"{surface_id}:{owner_id or 'none'}"


def _open_surface(
    registry: object,
    surface_id: str,
    owner_id: str,
    title: str,
    create: Callable[[], WindowT],
    refresh_existing: Callable[[WindowT], None] | None,
) -> WindowOpenResult[WindowT]:
    lifecycle = cast(_RegistryLifecycle[WindowT], registry)
    return lifecycle.open_or_raise(
        surface_key(surface_id, owner_id),
        title,
        create,
        refresh_existing=refresh_existing,
    )


__all__ = ["WindowSurfaceMixin", "surface_key"]
