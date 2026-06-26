"""Report output theme definitions."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class ReportTheme:
    """Portable visual palette for report exporters."""

    theme_id: str
    name: str
    background: str
    surface: str
    text: str
    muted_text: str
    accent: str
    border: str
    placeholder_fill: str
    placeholder_border: str
    table_header: str
    table_row: str


def built_in_report_themes() -> dict[str, ReportTheme]:
    """Return built-in report themes."""

    return {
        "light": ReportTheme(
            "light",
            "Light",
            "F7F8FA",
            "FFFFFF",
            "1F2937",
            "5B6472",
            "2563EB",
            "D6DAE1",
            "F8E9E9",
            "C2410C",
            "E9EEF6",
            "FFFFFF",
        ),
        "dark": ReportTheme(
            "dark",
            "Dark",
            "111827",
            "1F2937",
            "F8FAFC",
            "CBD5E1",
            "38BDF8",
            "475569",
            "2A1F23",
            "F97316",
            "263445",
            "1F2937",
        ),
    }


def report_theme(theme_id: str) -> ReportTheme:
    """Resolve a theme id, falling back to light."""

    themes = built_in_report_themes()
    return themes.get(theme_id, themes["light"])
