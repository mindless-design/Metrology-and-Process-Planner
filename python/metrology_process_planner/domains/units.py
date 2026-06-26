"""Canonical physical unit parsing and formatting."""

from __future__ import annotations

import re
from collections.abc import Mapping
from dataclasses import dataclass
from typing import Any

CANONICAL_LENGTH_UNIT = "um"
UNIT_AUTO = "auto"
SUPPORTED_LENGTH_UNITS = ("um", "Âµm", "micron", "microns", "nm", "A", "Ã…", "mm", "cm", "m")

_LENGTH_FACTORS_TO_UM = {
    "um": 1.0,
    "Âµm": 1.0,
    "Î¼m": 1.0,
    "nm": 0.001,
    "A": 0.0001,
    "Ã…": 0.0001,
    "â„«": 0.0001,
    "mm": 1000.0,
    "cm": 10000.0,
    "m": 1000000.0,
}
_UNIT_ALIASES = {
    "": "",
    "u": "um",
    "um": "um",
    "\u00b5m": "um",
    "\u03bcm": "um",
    "Âµm": "Âµm",
    "Î¼m": "Âµm",
    "micron": "um",
    "microns": "um",
    "micrometer": "um",
    "micrometers": "um",
    "nm": "nm",
    "nanometer": "nm",
    "nanometers": "nm",
    "a": "A",
    "\u00e5": "A",
    "\u00c5": "A",
    "\u212b": "A",
    "angstrom": "Ã…",
    "angstroms": "Ã…",
    "Ã¥": "Ã…",
    "â„«": "Ã…",
    "mm": "mm",
    "millimeter": "mm",
    "millimeters": "mm",
    "cm": "cm",
    "centimeter": "cm",
    "centimeters": "cm",
    "m": "m",
    "meter": "m",
    "meters": "m",
}
_QUANTITY_RE = re.compile(
    r"^\s*(?P<value>[+-]?(?:\d+(?:\.\d*)?|\.\d+)(?:[eE][+-]?\d+)?)"
    r"\s*(?P<unit>[A-Za-zÂµÎ¼Ã…Ã¥â„«]*)\s*$"
)


@dataclass(frozen=True)
class PhysicalQuantity:
    """A parsed length-like quantity stored in canonical micrometers."""

    value_um: float
    display_unit: str = CANONICAL_LENGTH_UNIT
    raw_text: str = ""

    @property
    def canonical_value(self) -> float:
        """Return the canonical numeric value in micrometers."""

        return self.value_um


class UnitParseError(ValueError):
    """Raised when a user-facing physical quantity cannot be parsed."""


def parse_length(
    value: Any,
    *,
    default_unit: str = CANONICAL_LENGTH_UNIT,
    allow_plain_angstrom: bool = False,
) -> PhysicalQuantity:
    """Parse a length value and return canonical micrometers."""

    if isinstance(value, PhysicalQuantity):
        return value
    if isinstance(value, Mapping):
        unit = value.get("unit", default_unit)
        raw_value = value.get("value", value.get("target", value.get("thickness")))
        if raw_value is None:
            raise UnitParseError(f"Could not parse length value: {value!r}.")
        return parse_length(
            raw_value,
            default_unit=str(unit or default_unit),
            allow_plain_angstrom=allow_plain_angstrom,
        )
    if isinstance(value, (int, float)):
        unit = canonical_length_unit(default_unit, allow_plain_angstrom=allow_plain_angstrom)
        return PhysicalQuantity(float(value) * _factor(unit), unit)
    text = _normalize_unit_text(str(value).strip())
    match = _QUANTITY_RE.match(text)
    if match is None:
        raise UnitParseError(f"Could not parse length value: {value!r}.")
    number = float(match.group("value"))
    raw_unit = match.group("unit")
    unit = (
        canonical_length_unit(raw_unit, allow_plain_angstrom=allow_plain_angstrom)
        if raw_unit
        else canonical_length_unit(default_unit, allow_plain_angstrom=allow_plain_angstrom)
    )
    return PhysicalQuantity(number * _factor(unit), unit, text)


def canonical_length_unit(unit: str, *, allow_plain_angstrom: bool = False) -> str:
    """Return a supported display unit token for a length unit string."""

    token = _normalize_unit_text(str(unit).strip())
    key = token.lower()
    if key == "a" and not allow_plain_angstrom:
        raise UnitParseError("Plain 'A' is ambiguous; use Ã… or angstrom in this context.")
    canonical = _UNIT_ALIASES.get(key)
    if canonical is None:
        raise UnitParseError(f"Unsupported length unit: {unit!r}.")
    return canonical or CANONICAL_LENGTH_UNIT


def _normalize_unit_text(text: str) -> str:
    return (
        text.replace("\u00c5", "angstrom")
        .replace("\u212b", "angstrom")
        .replace("\u00c3\u2026", "angstrom")
        .replace("\u0139", "angstrom")
        .replace("\u00c2", "")
        .replace("\u00b5", "u")
        .replace("\u03bc", "u")
    )


def is_supported_length_unit(unit: str, *, allow_plain_angstrom: bool = False) -> bool:
    """Return whether a length unit is supported in this context."""

    try:
        canonical_length_unit(unit, allow_plain_angstrom=allow_plain_angstrom)
    except UnitParseError:
        return False
    return True


def length_to_unit(value_um: float, unit: str) -> float:
    """Convert canonical micrometers to a supported display unit."""

    display_unit = canonical_length_unit(unit, allow_plain_angstrom=True)
    return float(value_um) / _factor(display_unit)


def format_length(
    value_um: float,
    *,
    display_unit: str = UNIT_AUTO,
    precision: int = 6,
) -> str:
    """Format a canonical micrometer value with a user-facing unit."""

    unit = auto_length_unit(value_um) if display_unit == UNIT_AUTO else canonical_length_unit(
        display_unit, allow_plain_angstrom=True
    )
    value = length_to_unit(value_um, unit)
    text = f"{value:.{precision}g}"
    return f"{text} {unit}"


def auto_length_unit(value_um: float) -> str:
    """Choose a readable display unit for a canonical micrometer value."""

    magnitude = abs(float(value_um))
    if magnitude == 0:
        return "nm"
    if magnitude < 1.0:
        return "nm"
    if magnitude >= 1000.0:
        return "mm"
    return "um"


def _factor(unit: str) -> float:
    return _LENGTH_FACTORS_TO_UM[unit]


from metrology_process_planner.domains.unit_diagnostics import (  # noqa: E402,F401
    UnitDiagnostic,
    length_diagnostics,
)
