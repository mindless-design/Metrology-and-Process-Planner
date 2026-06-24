"""Typed contracts for modeless application window ownership."""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Generic, Protocol, TypeVar

WindowT = TypeVar("WindowT")
WindowContra = TypeVar("WindowContra", contravariant=True)


class WindowOpenStatus(str, Enum):
    """Outcome for a modeless window open request."""

    CREATED = "created"
    RAISED = "raised"
    FAILED = "failed"


@dataclass(frozen=True)
class WindowRecord(Generic[WindowT]):
    """One tracked modeless application window."""

    key: str
    title: str
    window: WindowT
    revision: int = 1


@dataclass(frozen=True)
class WindowOpenResult(Generic[WindowT]):
    """Result returned after opening or raising a modeless window."""

    status: WindowOpenStatus
    key: str
    title: str = ""
    window: WindowT | None = None
    message: str = ""


class WindowLifecycleBackend(Protocol[WindowContra]):
    """Backend hooks for existing UI toolkits to manage top-level windows."""

    def is_alive(self, window: WindowContra) -> bool:
        """Return whether a tracked window can still be reused."""

    def raise_window(self, window: WindowContra) -> None:
        """Bring an existing window to the front."""
