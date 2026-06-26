"""Shared unit conversion helpers for CSV exporters."""

from __future__ import annotations

from typing import Any

from metrology_process_planner.domains.session.display_units import convert_length


def convert_optional_length(value: Any, canonical_unit: str, display_unit: str) -> Any:
    """Return a converted CSV value or an empty cell for missing input."""

    if value == "" or value is None:
        return ""
    return convert_length(float(value), canonical_unit, display_unit)


def convert_optional_length_text(value: Any, canonical_unit: str, display_unit: str) -> str:
    """Return a converted CSV value formatted as text."""

    converted = convert_optional_length(value, canonical_unit, display_unit)
    return "" if converted == "" else str(converted)
