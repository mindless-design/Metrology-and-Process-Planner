"""Shared models for repository quality tools."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]


@dataclass(frozen=True)
class QualityViolation:
    """One maintainability rule failure."""

    path: Path
    line: int
    rule: str
    message: str

    def format(self) -> str:
        """Return a compact command-line representation."""

        location = self.path.relative_to(PROJECT_ROOT)
        return f"{location}:{self.line}: {self.rule}: {self.message}"

