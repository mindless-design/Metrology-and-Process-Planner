"""Typed results returned by Advanced Diagnostics actions."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class DiagnosticsActionResult:
    """Structured modeless result for one diagnostics action."""

    action_id: str
    status: str
    message: str
    output_text: str = ""
    output_path: str = ""
    warning_ids: tuple[str, ...] = ()
    next_ui_hint: str = ""

    @property
    def ok(self) -> bool:
        """Return whether the action completed successfully."""

        return self.status == "success"


__all__ = ["DiagnosticsActionResult"]
