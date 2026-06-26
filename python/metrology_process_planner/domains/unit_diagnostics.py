"""Structured diagnostics for user-entered physical units."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from metrology_process_planner.domains.units import (
    CANONICAL_LENGTH_UNIT,
    PhysicalQuantity,
    UnitParseError,
    parse_length,
)


@dataclass(frozen=True)
class UnitDiagnostic:
    """Structured physical-unit diagnostic for recipe import and validation."""

    code: str
    severity: str
    message: str
    value: str = ""
    unit: str = ""
    repair_suggestion: str = ""


def length_diagnostics(
    value: Any,
    *,
    default_unit: str = CANONICAL_LENGTH_UNIT,
    allow_negative: bool = True,
    allow_zero: bool = True,
    allow_plain_angstrom: bool = False,
    suspicious_min_um: float | None = None,
    suspicious_max_um: float | None = 100000.0,
) -> tuple[UnitDiagnostic, ...]:
    """Return structured diagnostics for a user-entered length."""

    try:
        quantity = parse_length(
            value,
            default_unit=default_unit,
            allow_plain_angstrom=allow_plain_angstrom,
        )
    except UnitParseError as exc:
        return (_parse_error(value, exc),)
    return _quantity_diagnostics(
        value,
        quantity,
        allow_negative=allow_negative,
        allow_zero=allow_zero,
        suspicious_min_um=suspicious_min_um,
        suspicious_max_um=suspicious_max_um,
    )


def _quantity_diagnostics(
    value: Any,
    quantity: PhysicalQuantity,
    *,
    allow_negative: bool,
    allow_zero: bool,
    suspicious_min_um: float | None,
    suspicious_max_um: float | None,
) -> tuple[UnitDiagnostic, ...]:
    diagnostics: list[UnitDiagnostic] = []
    if quantity.value_um < 0 and not allow_negative:
        diagnostics.append(_negative(value, quantity))
    if quantity.value_um == 0 and not allow_zero:
        diagnostics.append(_zero(value, quantity))
    magnitude = abs(quantity.value_um)
    if suspicious_min_um is not None and magnitude and magnitude < suspicious_min_um:
        diagnostics.append(_suspicious(value, quantity, "below"))
    if suspicious_max_um is not None and magnitude > suspicious_max_um:
        diagnostics.append(_suspicious(value, quantity, "above"))
    return tuple(diagnostics)


def _parse_error(value: Any, exc: UnitParseError) -> UnitDiagnostic:
    return UnitDiagnostic(
        "LENGTH_PARSE_ERROR",
        "error",
        str(exc),
        value=str(value),
        repair_suggestion="Use a numeric value followed by a supported length unit.",
    )


def _negative(value: Any, quantity: PhysicalQuantity) -> UnitDiagnostic:
    return UnitDiagnostic(
        "LENGTH_NEGATIVE",
        "error",
        "Length must be non-negative.",
        value=str(value),
        unit=quantity.display_unit,
        repair_suggestion="Enter a zero or positive thickness.",
    )


def _zero(value: Any, quantity: PhysicalQuantity) -> UnitDiagnostic:
    return UnitDiagnostic(
        "LENGTH_ZERO",
        "error",
        "Length must be greater than zero.",
        value=str(value),
        unit=quantity.display_unit,
        repair_suggestion="Enter a non-zero thickness.",
    )


def _suspicious(value: Any, quantity: PhysicalQuantity, direction: str) -> UnitDiagnostic:
    return UnitDiagnostic(
        "LENGTH_SUSPICIOUS_MAGNITUDE",
        "warning",
        f"Length magnitude is {direction} the expected process range.",
        value=str(value),
        unit=quantity.display_unit,
        repair_suggestion="Check whether the entered unit is correct.",
    )
