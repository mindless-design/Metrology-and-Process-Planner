"""Small value helpers for process step models."""

from __future__ import annotations

from typing import Any, Optional


def optional_float(value: Any) -> Optional[float]:
    """Return a float for saved values, preserving missing values."""

    return None if value is None else float(value)


def optional_str(value: Any) -> Optional[str]:
    """Return a string for saved values, preserving missing values."""

    return None if value is None else str(value)


def bounded_value_warnings(
    lower: Optional[float],
    target: float,
    upper: Optional[float],
    label: str,
) -> tuple[str, ...]:
    """Return ordered-bound warnings for one scalar target/window."""

    checks = (
        (lower is not None and lower < 0, f"{label} lower bound must be non-negative."),
        (upper is not None and upper < 0, f"{label} upper bound must be non-negative."),
        (_limits_are_reversed(lower, upper), f"{label} lower bound is greater than upper bound."),
        (lower is not None and target < lower, f"{label} target is below lower bound."),
        (upper is not None and target > upper, f"{label} target is above upper bound."),
    )
    return tuple(message for failed, message in checks if failed)


def _limits_are_reversed(lower: Optional[float], upper: Optional[float]) -> bool:
    return lower is not None and upper is not None and lower > upper
