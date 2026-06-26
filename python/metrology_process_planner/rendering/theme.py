"""Shared visual theme contracts for generated engineering artifacts."""

from __future__ import annotations

from dataclasses import asdict, dataclass


@dataclass(frozen=True)
class RenderTheme:
    """Background-aware colors and typography for deterministic renderers."""

    theme_id: str
    background: str
    panel_fill: str
    panel_stroke: str
    primary_text: str
    secondary_text: str
    muted_text: str
    leader: str
    leader_warning: str
    warning_fill: str
    warning_text: str
    material_stroke: str
    scale_bar: str
    title_size_px: int = 22
    label_size_px: int = 15
    note_size_px: int = 14
    leader_width_px: float = 2.4
    panel_opacity: float = 0.9

    def to_dict(self) -> dict[str, object]:
        """Return JSON-compatible theme metadata."""

        return asdict(self)


ENGINEERING_DARK = RenderTheme(
    theme_id="engineering_dark",
    background="#0b1120",
    panel_fill="#111827",
    panel_stroke="#38bdf8",
    primary_text="#f8fafc",
    secondary_text="#bae6fd",
    muted_text="#cbd5e1",
    leader="#67e8f9",
    leader_warning="#fbbf24",
    warning_fill="#92400e",
    warning_text="#fff7ed",
    material_stroke="#e2e8f0",
    scale_bar="#f8fafc",
)


LIGHT = RenderTheme(
    theme_id="light",
    background="#ffffff",
    panel_fill="#ffffff",
    panel_stroke="#cbd5e1",
    primary_text="#0f172a",
    secondary_text="#334155",
    muted_text="#475569",
    leader="#0f766e",
    leader_warning="#b45309",
    warning_fill="#fffbeb",
    warning_text="#92400e",
    material_stroke="#334155",
    scale_bar="#0f172a",
    title_size_px=18,
    label_size_px=13,
    note_size_px=12,
    leader_width_px=1.4,
)


def render_theme(theme_id: str = "engineering_dark") -> RenderTheme:
    """Return a built-in render theme by id."""

    if theme_id == "light":
        return LIGHT
    return ENGINEERING_DARK


def contrast_text_for_fill(fill: str, theme: RenderTheme) -> str:
    """Return readable text color for a material swatch fill."""

    value = fill.lstrip("#")
    if len(value) != 6:
        return theme.primary_text
    r, g, b = (int(value[index:index + 2], 16) for index in (0, 2, 4))
    luminance = (0.299 * r + 0.587 * g + 0.114 * b) / 255.0
    return "#020617" if luminance > 0.62 else theme.primary_text
