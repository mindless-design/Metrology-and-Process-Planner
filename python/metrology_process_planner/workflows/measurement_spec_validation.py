"""Spec-limit validation helpers for measurement metadata edits."""

from __future__ import annotations


def spec_order_errors(
    measurement_id: str,
    target: float | None,
    lower: float | None,
    upper: float | None,
) -> tuple[str, ...]:
    """Return ordering errors for edited target and spec-limit values."""

    return tuple(
        message
        for message in (
            _spec_order_error(measurement_id, lower, upper),
            _target_lower_error(measurement_id, target, lower),
            _target_upper_error(measurement_id, target, upper),
        )
        if message
    )


def _spec_order_error(
    measurement_id: str,
    lower: float | None,
    upper: float | None,
) -> str:
    if lower is not None and upper is not None and lower > upper:
        return f"{measurement_id}: Lower spec limit is greater than upper spec limit."
    return ""


def _target_lower_error(
    measurement_id: str,
    target: float | None,
    lower: float | None,
) -> str:
    if target is not None and lower is not None and target < lower:
        return f"{measurement_id}: Target is below lower spec limit."
    return ""


def _target_upper_error(
    measurement_id: str,
    target: float | None,
    upper: float | None,
) -> str:
    if target is not None and upper is not None and target > upper:
        return f"{measurement_id}: Target is above upper spec limit."
    return ""
