"""Small scene assembly helpers for cross-section pipeline output."""

from __future__ import annotations

from metrology_process_planner.domains.process import ProcessFrame
from metrology_process_planner.rendering.cross_section.models import RenderIntent, RenderProfile
from metrology_process_planner.rendering.cross_section.scene_models import (
    CrossSectionSceneModel,
    LegendEntry,
    LegendModel,
    MaterialShape,
    PlacedLabel,
)


def axes(profile: RenderProfile) -> tuple[dict[str, object], ...]:
    """Return axis metadata for a render profile."""

    if profile.axis_policy == "none":
        return ()
    return ({"axis": "x", "units": "nm"}, {"axis": "z", "units": "nm"})


def scale_bars(profile: RenderProfile) -> tuple[dict[str, object], ...]:
    """Return scale bars required by physical render modes."""

    if profile.render_mode_id != "proportional_physical":
        return ()
    return ({"length": 100.0, "units": "nm", "label": "100 nm"},)


def leaders(labels: tuple[PlacedLabel, ...]) -> tuple[dict[str, object], ...]:
    """Return leader-line scene metadata from placed labels."""

    return tuple(
        {"target_id": label.target_id, "points": label.leader_line}
        for label in labels
        if getattr(label, "leader_line", None)
    )


def callouts(labels: tuple[PlacedLabel, ...]) -> tuple[dict[str, object], ...]:
    """Return callout scene metadata from placed labels."""

    return tuple(
        {"target_id": label.target_id, "text": label.text}
        for label in labels
        if getattr(label, "placement_type", "") == "callout"
    )


def legend(shapes: tuple[MaterialShape, ...], profile: RenderProfile) -> LegendModel:
    """Build a material legend for visible scene shapes."""

    entries: dict[str, LegendEntry] = {}
    for shape in shapes:
        if shape.material_id in entries:
            continue
        notes = ("exaggerated",) if shape.exaggerated_flag else ()
        entries[shape.material_id] = LegendEntry(
            shape.material_id,
            shape.material_name,
            shape.visual_style.get("fill", "#888888"),
            notes,
        )
    return LegendModel(
        tuple(entries.values()),
        compact=profile.legend_policy == "compact",
        show_exaggeration_notes=profile.thin_layer_policy.show_exaggeration_note,
        show_compression_notes=profile.compression_policy.show_compression_legend,
    )


def step_annotations(frame: ProcessFrame, profile: RenderProfile) -> tuple[dict[str, object], ...]:
    """Return step annotations for process-flow style scenes."""

    if not profile.label_policy.show_step_labels:
        return ()
    return ({"kind": "step_label", "step_id": frame.step_id, "text": frame.title},)


def highlights(intent: RenderIntent) -> tuple[dict[str, object], ...]:
    """Return selected-step highlight metadata."""

    if not intent.selected_process_step_id:
        return ()
    return (
        {
            "kind": intent.highlight_policy or "selected_step",
            "step_id": intent.selected_process_step_id,
        },
    )


def empty_scene(
    scene_id: str,
    profile: RenderProfile,
    title: str,
    warnings: tuple[str, ...],
) -> CrossSectionSceneModel:
    """Return a valid placeholder scene for empty solver output."""

    return CrossSectionSceneModel(
        scene_id,
        profile.render_mode_id,
        title or profile.display_name,
        "nm",
        "px",
        {},
        (),
        warnings=warnings,
    )
