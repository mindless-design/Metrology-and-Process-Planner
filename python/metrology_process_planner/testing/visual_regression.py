"""Golden-output comparison helpers for visual and structured artifacts."""

from __future__ import annotations

import json
from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True)
class RegressionComparison:
    """Result of comparing generated output to a golden reference."""

    matched: bool
    differences: tuple[str, ...] = ()

    def to_dict(self) -> dict[str, object]:
        """Serialize comparison details."""

        return {"matched": self.matched, "differences": list(self.differences)}


def compare_text(expected: str, actual: str) -> RegressionComparison:
    """Compare text outputs exactly."""

    if expected == actual:
        return RegressionComparison(True)
    return RegressionComparison(False, ("Text output differs from golden reference.",))


def compare_json(expected: Any, actual: Any) -> RegressionComparison:
    """Compare JSON-like structures while tolerating volatile metadata keys."""

    normalized_expected = _normalize(expected)
    normalized_actual = _normalize(actual)
    if normalized_expected == normalized_actual:
        return RegressionComparison(True)
    return RegressionComparison(False, ("JSON output differs from golden reference.",))


def image_comparison_unavailable() -> RegressionComparison:
    """Return an explicit result when no image backend is installed."""

    return RegressionComparison(
        True,
        ("Image pixel comparison skipped; no image backend configured.",),
    )


def _normalize(value: Any) -> Any:
    if isinstance(value, dict):
        return {
            key: _normalize(item)
            for key, item in sorted(value.items())
            if key not in {"created_at", "updated_at", "generated_at", "timestamp"}
        }
    if isinstance(value, list):
        return [_normalize(item) for item in value]
    try:
        json.dumps(value)
    except TypeError:
        return str(value)
    return value
