"""Serializable measurement annotation models for cross-section scenes."""

from __future__ import annotations

from collections.abc import Iterable, Sequence
from dataclasses import asdict, dataclass


@dataclass(frozen=True)
class MeasurementAnnotation:
    """One canonical measurement attached to a cross-section scene."""

    measurement_id: str
    kind: str
    label: str
    value: float
    unit: str
    formatted_value: str
    physical_span: tuple[tuple[float, float], tuple[float, float]]
    visual_span: tuple[tuple[float, float], tuple[float, float]]
    anchor_point: tuple[float, float]
    target_ids: tuple[str, ...] = ()
    caption: str = ""

    def to_dict(self) -> dict[str, object]:
        """Return JSON-compatible measurement metadata."""

        return asdict(self)


def measurement_from_dict(data: dict[str, object]) -> MeasurementAnnotation:
    """Build a measurement annotation from JSON-compatible data."""

    return MeasurementAnnotation(
        measurement_id=str(data.get("measurement_id", "")),
        kind=str(data.get("kind", "")),
        label=str(data.get("label", "")),
        value=_float_value(data.get("value", 0.0)),
        unit=str(data.get("unit", "um")),
        formatted_value=str(data.get("formatted_value", "")),
        physical_span=_span(data.get("physical_span")),
        visual_span=_span(data.get("visual_span")),
        anchor_point=_point(data.get("anchor_point")),
        target_ids=_string_tuple(data.get("target_ids")),
        caption=str(data.get("caption", "")),
    )


def _span(value: object) -> tuple[tuple[float, float], tuple[float, float]]:
    if not isinstance(value, Sequence) or isinstance(value, str) or len(value) != 2:
        return ((0.0, 0.0), (0.0, 0.0))
    return (_point(value[0]), _point(value[1]))


def _point(value: object) -> tuple[float, float]:
    if not isinstance(value, Sequence) or isinstance(value, str) or len(value) != 2:
        return (0.0, 0.0)
    return (_float_value(value[0]), _float_value(value[1]))


def _float_value(value: object) -> float:
    if isinstance(value, (int, float, str)):
        return float(value)
    return 0.0


def _string_tuple(value: object) -> tuple[str, ...]:
    if isinstance(value, str):
        return (value,) if value else ()
    if isinstance(value, Iterable):
        return tuple(str(item) for item in value)
    return ()
