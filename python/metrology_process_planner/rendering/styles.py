"""Drawing style value objects for render scenes."""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
from typing import Any, Optional


@dataclass(frozen=True)
class DrawingStyle:
    """Shared stroke, fill, opacity, and text settings."""

    stroke: str = "#ffcc00"
    fill: Optional[str] = None
    stroke_width: float = 2.0
    opacity: float = 1.0
    font_size_px: int = 14


def style_to_dict(style: DrawingStyle) -> dict[str, Any]:
    """Serialize a drawing style to JSON-compatible data."""

    return {
        "stroke": style.stroke,
        "fill": style.fill,
        "stroke_width": style.stroke_width,
        "opacity": style.opacity,
        "font_size_px": style.font_size_px,
    }


def style_from_dict(data: Mapping[str, Any]) -> DrawingStyle:
    """Build a drawing style from JSON-compatible data."""

    return DrawingStyle(
        stroke=str(data.get("stroke", "#ffcc00")),
        fill=_optional_str(data.get("fill")),
        stroke_width=float(data.get("stroke_width", 2.0)),
        opacity=float(data.get("opacity", 1.0)),
        font_size_px=int(data.get("font_size_px", 14)),
    )


def _optional_str(value: Any) -> Optional[str]:
    return None if value is None else str(value)
