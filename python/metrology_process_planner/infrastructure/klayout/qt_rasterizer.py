"""Qt-backed SVG rasterizer for KLayout runtime integration."""

from __future__ import annotations

from pathlib import Path
from typing import Any, Optional

from metrology_process_planner.infrastructure.klayout.plugin import import_pya


class QtSvgRasterizer:
    """Rasterize SVG text to PNG using Qt classes exposed by KLayout."""

    def __init__(self, pya_module: Optional[Any] = None) -> None:
        self._pya_module = pya_module

    def rasterize_svg(
        self,
        svg_text: str,
        destination: Path,
        width_px: int,
        height_px: int,
    ) -> None:
        """Render SVG text into a PNG file through Qt."""

        pya = self._pya()
        _require_qt_svg(pya)
        destination.parent.mkdir(parents=True, exist_ok=True)
        renderer = pya.QSvgRenderer(_byte_array(pya, svg_text))
        image = pya.QImage(width_px, height_px, pya.QImage.Format_ARGB32)
        image.fill(pya.QColor(255, 255, 255, 0))
        painter = pya.QPainter(image)
        try:
            renderer.render(painter)
        finally:
            painter.end()
        if not image.save(str(destination)):
            raise RuntimeError(f"Failed to save rasterized SVG to {destination}")

    def _pya(self) -> Any:
        return self._pya_module if self._pya_module is not None else import_pya()


def _require_qt_svg(pya: Any) -> None:
    required = ("QSvgRenderer", "QImage", "QPainter", "QColor")
    missing = [name for name in required if not hasattr(pya, name)]
    if missing:
        raise RuntimeError("KLayout Qt SVG support is missing: " + ", ".join(missing))


def _byte_array(pya: Any, svg_text: str) -> Any:
    data = svg_text.encode("utf-8")
    if hasattr(pya, "QByteArray"):
        return pya.QByteArray(data)
    return data
