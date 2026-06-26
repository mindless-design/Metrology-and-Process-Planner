"""Render-stage simplification policy and metadata helpers."""

from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import TYPE_CHECKING

from metrology_process_planner.rendering.cross_section.scene_models import MaterialShape

if TYPE_CHECKING:
    from metrology_process_planner.rendering.cross_section.filtering import FilterDiagnostics

SIMPLIFICATION_WARNING = "RENDER_SIMPLIFICATION_APPLIED"


@dataclass(frozen=True)
class RenderSimplificationPolicy:
    """Documented render transforms that improve clarity without changing solver geometry."""

    enabled: bool = False
    remove_redundant_regions: bool = False
    merge_same_material_runs: bool = False
    hide_irrelevant_buried_layers: bool = False
    simplify_tiny_slivers: bool = False
    preserve_critical_thin_layers: bool = True
    preserve_selected_feature_context: bool = True
    preserve_surface_profile: bool = False
    record_simplification_notes: bool = True


def simplification_annotations(
    policy: RenderSimplificationPolicy,
    diagnostics: tuple[FilterDiagnostics, ...],
    shapes: tuple[MaterialShape, ...],
) -> tuple[dict[str, object], ...]:
    """Return durable scene annotations for applied render simplification."""

    if not policy.enabled or not policy.record_simplification_notes:
        return ()
    notes = _notes(policy, diagnostics, shapes)
    if not notes:
        return ()
    return (
        {
            "kind": "render_simplification",
            "policy": asdict(policy),
            "notes": notes,
        },
    )


def simplification_warnings(
    policy: RenderSimplificationPolicy,
    diagnostics: tuple[FilterDiagnostics, ...],
    shapes: tuple[MaterialShape, ...],
) -> tuple[str, ...]:
    """Return warnings when render-only simplification changes visual presentation."""

    if simplification_annotations(policy, diagnostics, shapes):
        return (SIMPLIFICATION_WARNING,)
    return ()


def _notes(
    policy: RenderSimplificationPolicy,
    diagnostics: tuple[FilterDiagnostics, ...],
    shapes: tuple[MaterialShape, ...],
) -> tuple[str, ...]:
    notes = list(_policy_notes(policy, shapes))
    notes.extend(item.message for item in diagnostics if item.code.startswith("RENDER_"))
    return tuple(dict.fromkeys(notes))


def _policy_notes(
    policy: RenderSimplificationPolicy,
    shapes: tuple[MaterialShape, ...],
) -> tuple[str, ...]:
    checks = (
        (policy.hide_irrelevant_buried_layers,
         "irrelevant buried geometry hidden or reduced for readability"),
        (policy.merge_same_material_runs or policy.remove_redundant_regions,
         "redundant same-material regions may be merged in render space"),
        (policy.simplify_tiny_slivers, "sub-pixel visual slivers may be simplified"),
        (policy.preserve_critical_thin_layers and _has_thin_layer(shapes),
         "critical thin layers preserved for visibility"),
        (policy.preserve_surface_profile,
         "surface profile preserved as the primary visual reference"),
        (policy.preserve_selected_feature_context, "selected feature context preserved"),
    )
    return tuple(note for enabled, note in checks if enabled)


def _has_thin_layer(shapes: tuple[MaterialShape, ...]) -> bool:
    return any(shape.thin_layer_flag for shape in shapes)
