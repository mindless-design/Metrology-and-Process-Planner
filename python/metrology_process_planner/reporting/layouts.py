"""Reusable page and image layout descriptions."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class ImagePlacement:
    """Scaled image placement within a page layout."""

    x: float
    y: float
    width: float
    height: float
    notes_x: float = 0
    notes_y: float = 0


class ImageLayoutEngine:
    """Calculate aspect-preserving image placements for known layouts."""

    def placements(
        self,
        layout: str,
        image_count: int,
        page_width: float = 10.0,
        page_height: float = 7.5,
    ) -> tuple[ImagePlacement, ...]:
        """Return normalized placements for the requested layout."""

        if image_count <= 0:
            return ()
        if layout in {"two_column", "before_after"}:
            return self._grid(min(image_count, 2), 2, page_width, page_height)
        if layout in {"four_up", "gallery"}:
            return self._grid(min(image_count, 4), 2, page_width, page_height)
        if layout == "image_notes":
            return (ImagePlacement(0.6, 1.2, page_width * 0.58, page_height * 0.66, 6.7, 1.2),)
        if layout == "image_table":
            return (ImagePlacement(0.6, 1.1, page_width * 0.58, page_height * 0.58),)
        return (ImagePlacement(0.6, 1.1, page_width - 1.2, page_height - 1.8),)

    def _grid(
        self,
        image_count: int,
        columns: int,
        page_width: float,
        page_height: float,
    ) -> tuple[ImagePlacement, ...]:
        cell_width = (page_width - 1.4) / columns
        rows = 1 if image_count <= columns else 2
        cell_height = (page_height - 1.8) / rows
        placements: list[ImagePlacement] = []
        for index in range(image_count):
            column = index % columns
            row = index // columns
            placements.append(
                ImagePlacement(
                    0.6 + column * cell_width,
                    1.1 + row * cell_height,
                    cell_width,
                    cell_height,
                )
            )
        return tuple(placements)
