"""Render-note primitives for cross-section overlays."""

from __future__ import annotations

from metrology_process_planner.rendering.cross_section.models import CrossSectionOutputSpec
from metrology_process_planner.rendering.cross_section.scene_models import CrossSectionSceneModel
from metrology_process_planner.rendering.primitives import CanvasPoint, DrawingPrimitive, TextMark
from metrology_process_planner.rendering.styles import DrawingStyle
from metrology_process_planner.rendering.theme import RenderTheme


def note_primitives(
    scene: CrossSectionSceneModel,
    output_spec: CrossSectionOutputSpec,
    theme: RenderTheme,
) -> list[DrawingPrimitive]:
    """Return compression, exaggeration, and annotation notes."""

    notes = _scene_notes(scene)
    if not notes:
        return []
    y = output_spec.height_px - 20.0 - (len(notes) - 1) * 16.0
    return [
        _note_mark(note, y + index * 18.0, theme)
        for index, note in enumerate(notes[:4])
    ]


def _note_mark(note: str, y: float, theme: RenderTheme) -> TextMark:
    return TextMark(
        CanvasPoint(56.0, y),
        note,
        DrawingStyle(stroke=theme.secondary_text, fill=theme.secondary_text, font_size_px=14),
        anchor="start",
    )


def _scene_notes(scene: CrossSectionSceneModel) -> list[str]:
    notes = list(scene.compression_metadata.notes)
    legend = scene.legend
    if legend and legend.show_compression_notes and scene.compression_metadata.enabled:
        notes.append("Compressed stack view")
    if legend and legend.show_exaggeration_notes:
        notes.append("Thin layers exaggerated")
    notes.extend(str(item.get("text", "")) for item in scene.annotations if item.get("text"))
    return list(dict.fromkeys(note for note in notes if note))
