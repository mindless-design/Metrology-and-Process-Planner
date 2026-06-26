"""Shared session editor controller models."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any, Optional, Union

from metrology_process_planner.workflows.editor.document import SessionDocument

PathInput = Union[str, Path]


@dataclass(frozen=True)
class SessionEditorOpenResult:
    """Result of opening or resolving the unified session editor."""

    status: str
    message: str = ""
    document: Optional[SessionDocument] = None
    window: Optional[Any] = None
