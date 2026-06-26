"""SVG text helpers for capture visual polish artifacts."""

from __future__ import annotations

from html import escape

from metrology_process_planner.domains.session import ArtifactRecord
from metrology_process_planner.rendering.svg_text import hidden_text_element, text_image_element
from metrology_process_planner.rendering.theme import render_theme
from metrology_process_planner.rendering.visual_labels import LabelSpec

THEME = render_theme("engineering_dark")


def labeled_site_svg(
    raw: ArtifactRecord | None,
    label: LabelSpec,
    missing_raw: bool,
    image_href: str = "",
) -> str:
    """Return an SVG wrapper containing a site image and title strip."""

    width = raw.file.width_px if raw is not None and raw.file.width_px else 1024
    height = raw.file.height_px if raw is not None and raw.file.height_px else 768
    return "\n".join(
        (
            '<?xml version="1.0" encoding="UTF-8"?>',
            _svg_open(width, height),
            f'<rect x="0" y="0" width="{width}" height="{height}" fill="{THEME.background}" />',
            _site_image_svg(raw, width, height, image_href),
            (
                '<rect x="0" y="0" width="100%" height="96" '
                f'fill="{THEME.panel_fill}" opacity="{THEME.panel_opacity}" />'
            ),
            *label_text_lines(label, 18, 28),
            _source_warning_svg(missing_raw),
            "</svg>",
        )
    ) + "\n"


def placeholder_svg(label: LabelSpec, message: str) -> str:
    """Return a visual placeholder SVG for missing generated artifacts."""

    lines = label.text_lines or (label.label_id,)
    return "\n".join(
        (
            '<?xml version="1.0" encoding="UTF-8"?>',
            _placeholder_open(),
            f'<rect width="720" height="420" fill="{THEME.background}" />',
            _placeholder_frame(),
            _placeholder_title(lines[0]),
            _text_pair(message, 48, 112, 15, THEME.leader_warning),
            "</svg>",
        )
    ) + "\n"


def label_text_lines(label: LabelSpec, x: int, first_y: int) -> tuple[str, ...]:
    """Return SVG text elements for a multi-line label."""

    lines = []
    for index, text in enumerate(label.text_lines):
        weight = ' font-weight="700"' if index == 0 else ""
        size = 18 if index == 0 else 15
        lines.append(_text_pair(text, x, first_y + index * 18, size, THEME.primary_text, weight))
    return tuple(lines)


def _site_image_svg(
    raw: ArtifactRecord | None,
    width: int,
    height: int,
    image_href: str,
) -> str:
    if raw is None:
        return f'<rect x="0" y="0" width="{width}" height="{height}" fill="{THEME.background}" />'
    href = image_href or raw.relative_path
    return (
        f'<image href="{escape(href)}" xlink:href="{escape(href)}" x="0" y="0" width="{width}" '
        f'height="{height}" opacity="0.9" preserveAspectRatio="none" />'
    )


def _source_warning_svg(missing_raw: bool) -> str:
    if not missing_raw:
        return ""
    return _text_pair("Source image missing", 18, 104, 13, THEME.leader_warning)


def _svg_open(width: int, height: int) -> str:
    return (
        f'<svg xmlns="http://www.w3.org/2000/svg" '
        f'xmlns:xlink="http://www.w3.org/1999/xlink" width="{width}" height="{height}" '
        f'viewBox="0 0 {width} {height}" role="img">'
    )


def _placeholder_open() -> str:
    return (
        '<svg xmlns="http://www.w3.org/2000/svg" '
        'xmlns:xlink="http://www.w3.org/1999/xlink" width="720" height="420" '
        'viewBox="0 0 720 420" role="img">'
    )


def _placeholder_frame() -> str:
    return (
        '<rect x="24" y="24" width="672" height="372" fill="none" '
        f'stroke="{THEME.panel_stroke}" stroke-dasharray="8 6" />'
    )


def _placeholder_title(text: str) -> str:
    return (
        _text_pair(text, 48, 76, 22, THEME.primary_text, ' font-weight="700"')
    )


def _text_pair(
    text: str,
    x: float,
    y: float,
    font_size_px: float,
    fill: str,
    weight: str = "",
) -> str:
    return "\n".join(
        (
            text_image_element(text, x, y, font_size_px, fill),
            hidden_text_element(text, x, y, font_size_px, fill, weight=weight),
        )
    )
