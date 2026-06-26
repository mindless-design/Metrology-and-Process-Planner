"""Raster text fallback helpers for SVG renderers."""

from __future__ import annotations

import base64
from html import escape
from io import BytesIO

from PIL import Image, ImageColor, ImageDraw, ImageFont


def text_image_element(
    text: str,
    x: float,
    y: float,
    font_size_px: float,
    fill: str,
    anchor: str = "start",
) -> str:
    """Return an SVG image element containing readable rasterized text."""

    font = _font(font_size_px)
    left, top, right, bottom = ImageDraw.Draw(Image.new("RGBA", (1, 1))).textbbox(
        (0, 0),
        text,
        font=font,
    )
    width = max(1, right - left + 8)
    height = max(1, bottom - top + 8)
    image = Image.new("RGBA", (width, height), (255, 255, 255, 0))
    draw = ImageDraw.Draw(image)
    draw.text(
        (4 - left, 4 - top),
        text,
        font=font,
        fill=_color(fill),
        stroke_width=1,
        stroke_fill=(11, 17, 32, 220),
    )
    href = _data_uri(image)
    image_x = x - width / 2.0 if anchor == "middle" else x
    image_y = y - height + 4
    return (
        f'<image href="{href}" xlink:href="{href}" x="{_num(image_x)}" y="{_num(image_y)}" '
        f'width="{width}" height="{height}" preserveAspectRatio="none" />'
    )


def hidden_text_element(
    text: str,
    x: float,
    y: float,
    font_size_px: float,
    fill: str,
    anchor: str = "start",
    weight: str = "",
) -> str:
    """Return an invisible SVG text element for metadata and structural checks."""

    return (
        f'<text x="{_num(x)}" y="{_num(y)}" font-size="{_num(font_size_px)}" '
        f'text-anchor="{escape(anchor)}" font-family="Arial, Helvetica, sans-serif" '
        f'fill="{escape(fill)}" opacity="0"{weight}>{escape(text)}</text>'
    )


def _font(font_size_px: float) -> ImageFont.FreeTypeFont | ImageFont.ImageFont:
    size = max(8, int(round(font_size_px)))
    for name in ("arial.ttf", "DejaVuSans.ttf"):
        try:
            return ImageFont.truetype(name, size=size)
        except OSError:
            continue
    return ImageFont.load_default()


def _color(fill: str) -> tuple[int, int, int, int]:
    try:
        rgb = tuple(int(item) for item in ImageColor.getrgb(fill))
    except ValueError:
        rgb = (15, 23, 42)
    if len(rgb) == 4:
        return (rgb[0], rgb[1], rgb[2], rgb[3])
    return (rgb[0], rgb[1], rgb[2], 255)


def _data_uri(image: Image.Image) -> str:
    buffer = BytesIO()
    image.save(buffer, format="PNG")
    encoded = base64.b64encode(buffer.getvalue()).decode("ascii")
    return f"data:image/png;base64,{encoded}"


def _num(value: float) -> str:
    if float(value).is_integer():
        return str(int(value))
    return f"{value:.6f}".rstrip("0").rstrip(".")
