"""Display-unit preferences and engineering value formatting."""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
from typing import Any

from metrology_process_planner.domains.units import (
    UNIT_AUTO,
    UnitParseError,
    canonical_length_unit,
    length_to_unit,
    parse_length,
)
from metrology_process_planner.domains.units import (
    format_length as format_canonical_length,
)

DISPLAY_UNITS_EXTENSION_KEY = "display_units"
SUPPORTED_DISPLAY_UNITS = ("nm", "um", "mm", "layout", UNIT_AUTO)


@dataclass(frozen=True)
class DisplayUnitPreferences:
    """User-facing display choices that do not change canonical session values."""

    film_thickness: str = UNIT_AUTO
    layout_geometry: str = UNIT_AUTO
    cross_section_axes: str = UNIT_AUTO
    reports: str = UNIT_AUTO
    diagnostics: str = UNIT_AUTO

    @classmethod
    def from_dict(cls, data: Mapping[str, Any] | None) -> DisplayUnitPreferences:
        """Build display preferences from the session extension payload."""

        if not isinstance(data, Mapping):
            return cls()
        return cls(
            film_thickness=_normalized_preference(data.get("film_thickness", UNIT_AUTO)),
            layout_geometry=_normalized_preference(data.get("layout_geometry", UNIT_AUTO)),
            cross_section_axes=_normalized_preference(data.get("cross_section_axes", UNIT_AUTO)),
            reports=_normalized_preference(data.get("reports", UNIT_AUTO)),
            diagnostics=_normalized_preference(data.get("diagnostics", UNIT_AUTO)),
        )

    def to_dict(self) -> dict[str, str]:
        """Return the durable session-extension representation."""

        return {
            "film_thickness": self.film_thickness,
            "layout_geometry": self.layout_geometry,
            "cross_section_axes": self.cross_section_axes,
            "reports": self.reports,
            "diagnostics": self.diagnostics,
        }

    @property
    def is_default(self) -> bool:
        """Return whether all display choices preserve existing automatic behavior."""

        return all(value == UNIT_AUTO for value in self.to_dict().values())


def display_unit_preferences_from_session(session: Any) -> DisplayUnitPreferences:
    """Read display preferences from a session extension without mutating the session."""

    payload = dict(getattr(session, "extensions", {}) or {}).get(DISPLAY_UNITS_EXTENSION_KEY)
    return DisplayUnitPreferences.from_dict(payload if isinstance(payload, Mapping) else None)


def session_extensions_with_display_units(
    session: Any,
    preferences: DisplayUnitPreferences,
) -> dict[str, Any]:
    """Return session extensions with display preferences added, updated, or removed."""

    extensions = dict(getattr(session, "extensions", {}) or {})
    if preferences.is_default:
        extensions.pop(DISPLAY_UNITS_EXTENSION_KEY, None)
    else:
        extensions[DISPLAY_UNITS_EXTENSION_KEY] = preferences.to_dict()
    return extensions


def resolved_display_unit(
    value: float | None,
    canonical_unit: str,
    preference: str = UNIT_AUTO,
) -> str:
    """Return the concrete unit for an engineering value."""

    normalized = _normalized_preference(preference)
    canonical = _normalized_unit(canonical_unit)
    if normalized != UNIT_AUTO:
        return normalized
    if canonical == "layout":
        return canonical
    if value is None:
        return canonical
    return auto_display_unit(value, canonical)


def auto_display_unit(value: float | None, canonical_unit: str = "nm") -> str:
    """Choose a readable engineering length unit for a canonical value."""

    canonical = _normalized_unit(canonical_unit)
    if canonical == "layout":
        return "layout"
    magnitude_nm = abs(convert_length(value or 0.0, canonical, "nm"))
    if magnitude_nm >= 1_000_000.0:
        return "mm"
    if magnitude_nm >= 1_000.0:
        return "um"
    return "nm"


def convert_length(value: float, from_unit: str, to_unit: str) -> float:
    """Convert a length value between supported engineering units."""

    source = _normalized_unit(from_unit)
    target = _normalized_unit(to_unit)
    if source == target or source == "layout" or target == "layout":
        return value
    value_um = parse_length(
        {"value": value, "unit": source},
        default_unit=source,
        allow_plain_angstrom=True,
    ).value_um
    return length_to_unit(value_um, target)


def format_length(
    value: float | int | None,
    canonical_unit: str = "nm",
    preference: str = UNIT_AUTO,
    *,
    precision: int = 3,
    include_unit: bool = True,
) -> str:
    """Format a length for UI, report, or export display."""

    if value is None:
        return ""
    unit = resolved_display_unit(float(value), canonical_unit, preference)
    if unit == "layout":
        text = _format_number(float(value), precision)
        return f"{text} {unit}" if include_unit else text
    canonical_value_um = convert_length(float(value), canonical_unit, "um")
    formatted = format_canonical_length(
        canonical_value_um,
        display_unit=unit,
        precision=precision,
    )
    return formatted if include_unit else formatted.rsplit(" ", 1)[0]


def format_unit_summary(preferences: DisplayUnitPreferences) -> str:
    """Return a compact diagnostics label for active display-unit settings."""

    values = preferences.to_dict()
    if all(value == UNIT_AUTO for value in values.values()):
        return "auto"
    return ", ".join(f"{key}={value}" for key, value in values.items())


def _normalized_preference(value: Any) -> str:
    try:
        normalized = _normalized_unit(str(value or UNIT_AUTO))
    except UnitParseError:
        return UNIT_AUTO
    return normalized if normalized in SUPPORTED_DISPLAY_UNITS else UNIT_AUTO


def _normalized_unit(value: str) -> str:
    normalized = value.strip().lower().replace("µ", "u")
    if normalized in {"um", "micrometer", "micrometers", "micron", "microns"}:
        return "um"
    if normalized in {"nanometer", "nanometers"}:
        return "nm"
    if normalized in {"millimeter", "millimeters"}:
        return "mm"
    if normalized in {"layout", "dbu", "database"}:
        return "layout"
    if normalized == UNIT_AUTO:
        return UNIT_AUTO
    return canonical_length_unit(normalized, allow_plain_angstrom=True)


def _format_number(value: float, precision: int) -> str:
    text = f"{value:.{precision}f}".rstrip("0").rstrip(".")
    return text or "0"
