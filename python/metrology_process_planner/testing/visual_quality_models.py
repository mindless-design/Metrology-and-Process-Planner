"""Shared model aliases for visual quality helpers."""

from __future__ import annotations

from dataclasses import asdict, dataclass


@dataclass(frozen=True)
class VisualIssue:
    """One machine-readable visual QA issue."""

    issue_id: str
    visual_path: str
    visual_type: str
    severity: str
    category: str
    description: str
    likely_cause: str
    recommended_fix: str
    status: str = "open"

    def to_dict(self) -> dict[str, str]:
        """Return JSON-compatible issue data."""

        return asdict(self)
