"""pyxs/xsection compatibility planning seam."""

from __future__ import annotations

from metrology_process_planner.domains.process.recipe import ProcessRecipe
from metrology_process_planner.domains.process.steps import ProcessStepKind
from metrology_process_planner.solver.solver_outputs import RecipeToPyxsPlan

_PYXS_MAPPED = {
    ProcessStepKind.SUBSTRATE,
    ProcessStepKind.BLANKET_DEPOSITION,
    ProcessStepKind.PATTERNED_DEPOSITION,
    ProcessStepKind.DIRECTIONAL_ETCH,
    ProcessStepKind.PLANARIZATION,
}


def build_recipe_to_pyxs_plan(recipe: ProcessRecipe) -> RecipeToPyxsPlan:
    """Classify recipe operations by pyxs-style compatibility."""

    mapped = []
    internal = []
    notes = []
    for step in recipe.steps:
        if step.kind in _PYXS_MAPPED:
            mapped.append(step.id)
        else:
            internal.append(step.id)
            notes.append(f"{step.id}: {step.kind.value} uses Process Planner internal semantics.")
    return RecipeToPyxsPlan(tuple(mapped), tuple(internal), tuple(notes))
