"""Shared fixtures for hybrid solver tests."""

from __future__ import annotations

from metrology_process_planner.domains.process import (
    HybridCrossSectionSolver,
    MaskPolarity,
    Material,
    ProcessRecipe,
    ProcessStep,
    ProcessStepKind,
    ProcessWindow,
    SolverInput,
    SolverOptions,
    ThicknessSpec,
)


def _solve(recipe: ProcessRecipe):
    return HybridCrossSectionSolver().solve(SolverInput(recipe, SolverOptions(sample_count=21)))


def _recipe(*steps: ProcessStep) -> ProcessRecipe:
    materials = (
        Material("si", "Silicon", "#777777"),
        Material("oxide", "Oxide", "#55aaff"),
        Material("nitride", "Nitride", "#ffaa00"),
        Material("metal", "Metal", "#bbbbbb"),
    )
    return ProcessRecipe("fixture", "Fixture", materials, steps)


def _substrate() -> ProcessStep:
    return ProcessStep("substrate", ProcessStepKind.SUBSTRATE, "si", ThicknessSpec(1.0))


def _blanket(material_id: str, thickness: float) -> ProcessStep:
    return ProcessStep(
        material_id,
        ProcessStepKind.BLANKET_DEPOSITION,
        material_id,
        ThicknessSpec(thickness),
    )


def _patterned(material_id, mask, polarity=MaskPolarity.DIRECT) -> ProcessStep:
    return ProcessStep(
        material_id,
        ProcessStepKind.PATTERNED_DEPOSITION,
        material_id,
        ThicknessSpec(0.5),
        mask_polarity=polarity,
        mask_intervals=mask,
    )


def _cmp(dishing: float) -> ProcessStep:
    from metrology_process_planner.domains.process import PlanarizationProfile

    profile = PlanarizationProfile(1.4, ("metal",), dishing_coefficient=dishing)
    return ProcessStep("cmp", ProcessStepKind.CMP_PLANARIZATION, planarization_profile=profile)


def _window() -> ProcessWindow:
    return ProcessWindow("thickness", 0.1, 0.2, 0.3)


def _stack(result, x: float):
    column = min(result.frames[-1].profile.columns, key=lambda item: abs(item.x - x))
    return column.intervals


def _top(result, x: float) -> float:
    return max(interval.z_max for interval in _stack(result, x))


def _codes(result) -> set[str]:
    return {item.code for item in result.diagnostics}
