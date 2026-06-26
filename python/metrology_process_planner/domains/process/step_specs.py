"""Thickness and process-window value objects for process steps."""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
from typing import Any, Optional

from metrology_process_planner.domains.process.step_values import bounded_value_warnings
from metrology_process_planner.domains.units import (
    CANONICAL_LENGTH_UNIT,
    UnitParseError,
    canonical_length_unit,
    parse_length,
)


@dataclass(frozen=True)
class ThicknessSpec:
    """Nominal and optional bounded thickness for a process step."""

    target: float
    lower: Optional[float] = None
    upper: Optional[float] = None
    unit: str = CANONICAL_LENGTH_UNIT
    display_unit: str = ""

    def __post_init__(self) -> None:
        display_unit = self.display_unit or self.unit
        try:
            unit = canonical_length_unit(self.unit, allow_plain_angstrom=True)
            display_unit = canonical_length_unit(display_unit, allow_plain_angstrom=True)
        except UnitParseError:
            return
        if unit == CANONICAL_LENGTH_UNIT:
            object.__setattr__(self, "unit", CANONICAL_LENGTH_UNIT)
            object.__setattr__(self, "display_unit", display_unit)
            return
        object.__setattr__(
            self, "target", parse_length(self.target, default_unit=unit,
                                          allow_plain_angstrom=True).value_um
        )
        object.__setattr__(self, "lower", _normalized_optional_length(self.lower, unit))
        object.__setattr__(self, "upper", _normalized_optional_length(self.upper, unit))
        object.__setattr__(self, "unit", CANONICAL_LENGTH_UNIT)
        object.__setattr__(self, "display_unit", display_unit)

    def validate(self) -> tuple[str, ...]:
        """Return warnings for inconsistent thickness limits."""

        warnings: list[str] = []
        try:
            canonical_length_unit(self.unit, allow_plain_angstrom=True)
            if self.display_unit:
                canonical_length_unit(self.display_unit, allow_plain_angstrom=True)
        except UnitParseError as error:
            warnings.append(str(error))
        if self.target < 0:
            warnings.append("Thickness target must be non-negative.")
        warnings.extend(bounded_value_warnings(self.lower, self.target, self.upper, "Thickness"))
        return tuple(warnings)

    def to_dict(self) -> dict[str, Any]:
        """Serialize the thickness spec to JSON-compatible data."""

        return {
            "target": self.target,
            "lower": self.lower,
            "upper": self.upper,
            "unit": self.unit,
            "display_unit": self.display_unit or self.unit,
        }

    @classmethod
    def from_dict(cls, data: Mapping[str, Any]) -> ThicknessSpec:
        """Build a thickness spec from saved JSON-compatible data."""

        unit = str(data.get("unit", CANONICAL_LENGTH_UNIT))
        display_unit = str(data.get("display_unit", unit))
        try:
            target = parse_length(data["target"], default_unit=unit, allow_plain_angstrom=True)
            lower = _parsed_optional_length(data.get("lower"), unit)
            upper = _parsed_optional_length(data.get("upper"), unit)
        except UnitParseError:
            return cls(
                target=float(data["target"]),
                lower=_optional_float(data.get("lower")),
                upper=_optional_float(data.get("upper")),
                unit=unit,
                display_unit=display_unit,
            )
        return cls(
            target=target.value_um,
            lower=lower,
            upper=upper,
            unit=CANONICAL_LENGTH_UNIT,
            display_unit=target.display_unit or display_unit,
        )


@dataclass(frozen=True)
class ProcessWindow:
    """Lower, target, and upper value for process planning."""

    name: str
    lower: float
    target: float
    upper: float
    unit: str = CANONICAL_LENGTH_UNIT
    display_unit: str = ""

    def __post_init__(self) -> None:
        display_unit = self.display_unit or self.unit
        try:
            unit = canonical_length_unit(self.unit, allow_plain_angstrom=True)
            display_unit = canonical_length_unit(display_unit, allow_plain_angstrom=True)
        except UnitParseError:
            return
        if unit != CANONICAL_LENGTH_UNIT:
            object.__setattr__(self, "lower", _parsed_required_length(self.lower, unit))
            object.__setattr__(self, "target", _parsed_required_length(self.target, unit))
            object.__setattr__(self, "upper", _parsed_required_length(self.upper, unit))
        object.__setattr__(self, "unit", CANONICAL_LENGTH_UNIT)
        object.__setattr__(self, "display_unit", display_unit)

    def validate(self) -> tuple[str, ...]:
        """Return warnings when a process window is not ordered."""

        warnings: list[str] = []
        try:
            canonical_length_unit(self.unit, allow_plain_angstrom=True)
            if self.display_unit:
                canonical_length_unit(self.display_unit, allow_plain_angstrom=True)
        except UnitParseError as error:
            warnings.append(str(error))
        if self.lower <= self.target <= self.upper:
            return tuple(warnings)
        warnings.append("Process window must satisfy lower <= target <= upper.")
        return tuple(warnings)

    def to_dict(self) -> dict[str, Any]:
        """Serialize the process window to JSON-compatible data."""

        return {
            "name": self.name,
            "lower": self.lower,
            "target": self.target,
            "upper": self.upper,
            "unit": self.unit,
            "display_unit": self.display_unit or self.unit,
        }

    @classmethod
    def from_dict(cls, data: Mapping[str, Any]) -> ProcessWindow:
        """Build a process window from saved JSON-compatible data."""

        unit = str(data.get("unit", CANONICAL_LENGTH_UNIT))
        display_unit = str(data.get("display_unit", unit))
        try:
            lower = parse_length(data["lower"], default_unit=unit, allow_plain_angstrom=True)
            target = parse_length(data["target"], default_unit=unit, allow_plain_angstrom=True)
            upper = parse_length(data["upper"], default_unit=unit, allow_plain_angstrom=True)
        except UnitParseError:
            return cls(
                name=str(data["name"]),
                lower=float(data["lower"]),
                target=float(data["target"]),
                upper=float(data["upper"]),
                unit=unit,
                display_unit=display_unit,
            )
        return cls(
            name=str(data["name"]),
            lower=lower.value_um,
            target=target.value_um,
            upper=upper.value_um,
            unit=CANONICAL_LENGTH_UNIT,
            display_unit=display_unit,
        )


def _parsed_required_length(value: float, unit: str) -> float:
    return parse_length(value, default_unit=unit, allow_plain_angstrom=True).value_um


def _parsed_optional_length(value: Any, unit: str) -> Optional[float]:
    if value is None:
        return None
    return parse_length(value, default_unit=unit, allow_plain_angstrom=True).value_um


def _normalized_optional_length(value: Optional[float], unit: str) -> Optional[float]:
    if value is None:
        return None
    return _parsed_required_length(value, unit)


def _optional_float(value: Any) -> Optional[float]:
    if value is None:
        return None
    return float(value)
