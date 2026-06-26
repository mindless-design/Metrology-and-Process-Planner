"""Render visual quality gallery SVGs into PNG previews and a contact sheet."""

from __future__ import annotations

import os
import sys
from pathlib import Path

from PIL import Image, ImageDraw

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_GALLERY_ROOT = ROOT / "tests" / "output" / "visual_review_gallery"


def main(argv: list[str] | None = None) -> None:
    """Render SVG previews and write a review contact sheet."""

    args = argv if argv is not None else sys.argv[1:]
    gallery_root = Path(args[0]) if args else DEFAULT_GALLERY_ROOT
    render_visual_quality_previews(gallery_root)


def render_visual_quality_previews(gallery_root: Path) -> Path:
    """Render all gallery SVGs and return the contact sheet path."""

    preview_root = gallery_root / "rendered_previews"
    preview_root.mkdir(parents=True, exist_ok=True)
    _render_svgs(gallery_root, preview_root)
    return build_contact_sheet(gallery_root, preview_root)


def build_contact_sheet(gallery_root: Path, preview_root: Path) -> Path:
    """Build a single contact sheet containing raw and rendered gallery images."""

    sources = _contact_sheet_sources(gallery_root, preview_root)
    thumbs = [_thumbnail(gallery_root, source) for source in sources]
    columns = 3
    rows = max(1, (len(thumbs) + columns - 1) // columns)
    width, height = _tile_size()
    sheet = Image.new("RGB", (columns * width, rows * height), (226, 232, 240))
    for index, thumb in enumerate(thumbs):
        sheet.paste(thumb, ((index % columns) * width, (index // columns) * height))
    output = preview_root / "contact_sheet.png"
    sheet.save(output)
    return output


def _render_svgs(gallery_root: Path, preview_root: Path) -> None:
    os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

    from PyQt5.QtCore import QSize
    from PyQt5.QtGui import QImage, QPainter
    from PyQt5.QtSvg import QSvgRenderer
    from PyQt5.QtWidgets import QApplication

    app = QApplication.instance() or QApplication([])
    for svg_path in _svg_paths(gallery_root):
        renderer = QSvgRenderer(str(svg_path))
        size = renderer.defaultSize()
        if not size.isValid() or size.width() <= 0 or size.height() <= 0:
            size = QSize(1024, 768)
        image = QImage(size, QImage.Format_ARGB32)
        image.fill(0xFFFFFFFF)
        painter = QPainter(image)
        renderer.render(painter)
        painter.end()
        image.save(str(_preview_path(gallery_root, preview_root, svg_path)))
    app.quit()


def _svg_paths(gallery_root: Path) -> tuple[Path, ...]:
    return tuple(
        sorted(
            path
            for path in gallery_root.rglob("*.svg")
            if "rendered_previews" not in path.parts
        )
    )


def _preview_path(gallery_root: Path, preview_root: Path, svg_path: Path) -> Path:
    name = str(svg_path.relative_to(gallery_root)).replace("\\", "__").replace("/", "__")
    return preview_root / f"{name}.png"


def _contact_sheet_sources(gallery_root: Path, preview_root: Path) -> tuple[Path, ...]:
    raw_images = tuple(sorted((gallery_root / "images").glob("*.png")))
    previews = tuple(
        path
        for path in sorted(preview_root.glob("*.png"))
        if path.name not in {"contact_sheet.png", "font_probe.png"}
    )
    return raw_images + previews


def _thumbnail(gallery_root: Path, source: Path) -> Image.Image:
    width, height = _tile_size()
    label_height = 42
    image = Image.open(source).convert("RGB")
    image.thumbnail((width, height - label_height))
    canvas = Image.new("RGB", (width, height), "white")
    x = (width - image.width) // 2
    y = label_height + (height - label_height - image.height) // 2
    canvas.paste(image, (x, y))
    label = str(source.relative_to(gallery_root))
    ImageDraw.Draw(canvas).text((8, 8), label[:52], fill=(15, 23, 42))
    return canvas


def _tile_size() -> tuple[int, int]:
    return (360, 260)


if __name__ == "__main__":
    main()
