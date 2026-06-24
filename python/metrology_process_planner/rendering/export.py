"""Drawing scene export orchestration and rasterizer contracts."""

from __future__ import annotations

import json
import traceback
from dataclasses import dataclass
from pathlib import Path
from typing import Optional, Protocol

from metrology_process_planner.rendering.scene import DrawingScene, scene_to_dict
from metrology_process_planner.rendering.svg_renderer import render_scene_to_svg


class SvgRasterizer(Protocol):
    """Boundary protocol for converting SVG text to a raster image."""

    def rasterize_svg(
        self,
        svg_text: str,
        destination: Path,
        width_px: int,
        height_px: int,
    ) -> None:
        """Render SVG text to a raster image destination."""


@dataclass(frozen=True)
class DrawingExportResult:
    """Metadata returned after writing drawing scene artifacts."""

    spec_path: Path
    svg_path: Path
    png_path: Optional[Path]
    width_px: int
    height_px: int
    warnings: tuple[str, ...] = ()
    diagnostics: tuple[ExportDiagnostic, ...] = ()


@dataclass(frozen=True)
class ExportDiagnostic:
    """Structured diagnostic detail for a non-fatal export failure."""

    message: str
    exception_type: str = ""
    exception_message: str = ""
    stack_trace: str = ""


class DrawingExporter:
    """Write editable drawing specs, SVG, and optional raster output."""

    def export(
        self,
        scene: DrawingScene,
        spec_path: Path,
        svg_path: Path,
        png_path: Optional[Path] = None,
        rasterizer: Optional[SvgRasterizer] = None,
    ) -> DrawingExportResult:
        """Write drawing scene artifacts and return their locations."""

        spec_path.parent.mkdir(parents=True, exist_ok=True)
        svg_path.parent.mkdir(parents=True, exist_ok=True)
        _write_json(scene, spec_path)
        svg_text = render_scene_to_svg(scene)
        svg_path.write_text(svg_text, encoding="utf-8")
        raster = _rasterize_png(scene, svg_text, png_path, rasterizer)
        return DrawingExportResult(
            spec_path=spec_path,
            svg_path=svg_path,
            png_path=raster.png_path,
            width_px=scene.canvas.width_px,
            height_px=scene.canvas.height_px,
            warnings=raster.warnings,
            diagnostics=raster.diagnostics,
        )


@dataclass(frozen=True)
class _RasterExport:
    png_path: Optional[Path]
    warnings: tuple[str, ...] = ()
    diagnostics: tuple[ExportDiagnostic, ...] = ()


def _rasterize_png(
    scene: DrawingScene,
    svg_text: str,
    png_path: Optional[Path],
    rasterizer: Optional[SvgRasterizer],
) -> _RasterExport:
    if png_path is None:
        return _RasterExport(None)
    if rasterizer is None:
        message = "PNG output skipped because no SVG rasterizer was provided."
        return _RasterExport(None, (message,), (ExportDiagnostic(message=message),))
    png_path.parent.mkdir(parents=True, exist_ok=True)
    try:
        rasterizer.rasterize_svg(svg_text, png_path, scene.canvas.width_px, scene.canvas.height_px)
    except Exception as exc:  # noqa: BLE001 - rasterizers are infrastructure adapters.
        message = f"PNG rasterization failed: {exc}"
        return _RasterExport(None, (message,), (_export_exception(message, exc),))
    return _RasterExport(png_path)


def _export_exception(message: str, exc: BaseException) -> ExportDiagnostic:
    return ExportDiagnostic(
        message=message,
        exception_type=type(exc).__name__,
        exception_message=str(exc),
        stack_trace="".join(traceback.format_exception(type(exc), exc, exc.__traceback__)),
    )


def _write_json(scene: DrawingScene, destination: Path) -> None:
    with destination.open("w", encoding="utf-8") as handle:
        json.dump(scene_to_dict(scene), handle, indent=2, sort_keys=True)
        handle.write("\n")
