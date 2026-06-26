# Solver Invariants

Last updated: 2026-06-24

## Stack Invariants

`StackInvariantChecker` enforces the invariants needed before renderer handoff:

1. Stack geometry must contain columns.
2. Column x positions must be deterministic and increasing.
3. Material intervals must satisfy `z_max > z_min`.
4. Material intervals must have material IDs.
5. Material IDs must resolve when a material ID set is supplied.
6. Intervals within one column must not overlap.
7. The top surface must be computable from interval tops.
8. Surface profile points must match `(column.x, column.top)`.
9. Process frames must preserve increasing recipe step order when step indexes are present.
10. Process frames must carry a stack signature.

Violations return `SolverDiagnostic` records with code `STACK_INVARIANT_VIOLATION` and
`output_usable=False`.

## Hidden Materials

Hidden materials remain physical. If a hidden material reaches the top of any column, the solver
emits `HIDDEN_MATERIAL_AFFECTS_HEIGHT`. Renderers may choose not to draw hidden materials, but they
must not collapse their physical height unless a later projection explicitly marks that material as
display-only.

## Surface Profile

The surface profile is derived from the stack model. Renderer-facing surface data should be treated
as a projection of `StackGeometry2D`, not a separate authority.

## Stack Signature

The sampled backend computes stack signatures from x positions and material intervals. Identical
input recipe/options/backend/unit values should produce identical signatures.

## Strict Mode

Set `SolverOptions.strict_mode=True` to:

- run `StackInvariantChecker.check_stack_model()` after each step.
- validate final render projections.
- preserve debug metadata in frame/result fields.
- convert architecture bugs into structured blocking diagnostics instead of silent renderer
  failures.

Normal mode still returns diagnostics for invalid input but does not run every invariant check after
every step.
