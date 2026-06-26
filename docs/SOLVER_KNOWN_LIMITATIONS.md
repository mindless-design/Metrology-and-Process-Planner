# Solver Known Limitations

Last updated: 2026-06-24

## Backend Scope

The active backend is sampled-column geometry. It is deterministic and render-ready, but it is not a
full process simulator and cannot represent every 2D topology exactly.

## Operation Limitations

- Substrate: establishes a flat `z=0..thickness` reference. Negative/zero thickness is rejected or
  caught by invariant checks.
- Blanket deposition: follows sampled local topography and preserves hidden material height.
- Patterned deposition: supports direct and inverted `MaskInterval` masks. Inline mask intervals
  can run without live KLayout geometry; missing layer references remain diagnostics.
- Conformal deposition: uses top/sidewall/bottom coverage factors in sampled columns. It emits
  `CONFORMAL_APPROXIMATION_USED`; pinch-off is represented by diagnostics, not a solved seam mesh.
- Directional etch: removes target material top-down in sampled columns. Exhaustion and blocker
  warnings need more complete operation-level accounting.
- Isotropic etch: approximates lateral attack using sampled x positions and emits
  `ISOTROPIC_UNDERCUT_APPROXIMATED`.
- Tapered etch: emits `TAPERED_PROFILE_APPROXIMATED`, but current regions are rectangular sampled
  intervals. Polygonal tapered sidewalls require a future projection shape model.
- Planarization: clips stacks to target or median height.
- CMP planarization: applies explicit overpolish/dishing/erosion heuristics and emits
  `CMP_DISHING_HEURISTIC_USED`.
- Annotation-only: preserves stack geometry and marks `changed_from_previous=False` on frames.

## Process Windows

`solve_variants()` currently emits deterministic labels for lower/target/upper process-window
variants. It does not yet substitute process-window values into operation parameters.

## Fixture Coverage Gaps

Existing fixtures cover successful synthetic recipes, render profiles, and operation smoke tests.
The following fixture families should be expanded as stable JSON snapshots:

- excessive etch depth.
- directional etch blocked by non-target material.
- narrow conformal gap pinch-off with renderer-facing warning assertions.
- invalid process-window and invalid-unit cases.
- point-stack membership for multiple material transitions.
- explicit FIB full-stack projection contract validation.

## Renderer Impact

Renderers can consume current outputs without guessing material identity, units, top surface,
physical bounds, or diagnostic state. Renderers must still respect approximation diagnostics for
conformal, isotropic, tapered, and CMP outputs and should avoid presenting those views as
process-physics exact.
