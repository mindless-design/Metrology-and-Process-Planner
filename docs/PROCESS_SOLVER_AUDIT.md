# Process Solver Audit

Last updated: 2026-06-24

## Stop/Go Assessment

Status: go for renderer integration through the documented `SolverResult` and
`RenderProjection` contracts.

The solver is pure Python, deterministic for identical recipe/options input, and now emits
render-ready metadata at result and frame boundaries. The renderer should consume public process
models only; it should not inspect private solver helpers or recipe internals to resolve material
identity, units, diagnostics, or physical bounds.

Remaining caveat: the sampled-column backend is a communication-grade geometry model, not a
process-physics simulator. Conformal, isotropic, tapered, and CMP behavior are explicit
approximations and must stay labeled in diagnostics/reporting.

## Architecture Map

- `recipe.py`, `steps.py`, `materials.py`: pure recipe and material data.
- `solver_outputs.py`, `geometry_models.py`, `solver_profiles.py`: public solver input/output
  models, stack geometry, process frames, render projections, options, profiles, and diagnostics.
- `geometry_kernel.py`: backend protocol for stack mutation and extraction.
- `sampled_geometry_kernel.py`, `sampled_geometry_helpers.py`: current sampled-column backend.
- `operations.py`, `operation_helpers.py`: modular operation executors.
- `hybrid_solver.py`: orchestration, input validation, frame capture, strict-mode checks, final
  result assembly.
- `solver_validation.py`: structured input validation diagnostics.
- `invariants.py`: stack and frame invariant checks.
- `render_contract.py`: render projection type list and projection validator.
- `pyxs_compat.py`: compatibility planning notes for later pyxs comparison.

## Boundary Audit

- KLayout `pya` imports in solver core: none found.
- Qt/UI imports in solver core: none found.
- Direct image drawing/export in solver core: none found.
- Session JSON mutation in solver core: none found.
- Artifact record writes in solver core: none found.
- Geometry extraction is separate from solving through `GeometryKernel` point and cutline APIs.
- Multiple backends can coexist through the `GeometryKernel` protocol and `KernelFactory`.
- Backend-normalized output is provided through `SolverResult`, `ProcessFrame`, and
  `RenderProjection`.

Coverage: `tests/test_solver_contract.py` includes AST boundary checks for KLayout/Qt imports and
renderer/export calls.

## Current Backend List

- `SampledGeometryKernel`: sampled 2D stack columns over `x_min..x_max`.

No pyxs backend is active. `pyxs_compat.py` currently produces planning metadata only.

## Operation Executor List

- `SubstrateOperation`
- `BlanketDepositOperation`
- `PatternedDepositOperation`
- `ConformalDepositOperation`
- `DirectionalEtchOperation`
- `IsotropicEtchOperation`
- `TaperedEtchOperation`
- `PlanarizeOperation`
- `CMPPlanarizeOperation`
- `AnnotationOnlyOperation`

## Current Stack Representation

The canonical solved stack is `StackGeometry2D(columns)`. Each `StackColumn` owns ordered
`MaterialInterval(material_id, z_min, z_max)` values. Top surface is derived as
`SurfaceProfile((x, column.top))`. Render regions are generated as rectangular
`MaterialRegion(material_id, x_min, x_max, z_min, z_max)` records.

Units are explicit on `SolverInput.units`, `SolverResult.units`, and `RenderProjection.units`.
Current default is `um`.

## Renderer-Facing Outputs

Every successful solve now populates:

- `SolverResult.final_stack`
- `SolverResult.render_projections`
- `SolverResult.material_metadata`
- `SolverResult.point_samples`
- `SolverResult.cutline_samples`
- `SolverResult.frames`
- `SolverResult.diagnostics`
- `SolverResult.approximation_notes`
- `SolverResult.metrics`

Each `RenderProjection` carries material metadata, material order, material regions, surface
profile, physical bounds, units, hidden material IDs, changed regions, warnings, compression/thin
layer hint maps, and approximation notes.

## Diagnostics Audit

Structured diagnostics include severity, code, step ID, message, technical details, suggested
repair, output usability, diagnostic ID, and step name. Diagnostics are preserved into
`SolverResult`, `ProcessFrame`, and `RenderProjection.warnings`.

Supported or mapped codes now include:

- `MISSING_LAYER`
- `EMPTY_MASK`
- `STEP_DISABLED`
- `UNSUPPORTED_OPERATION`
- `UNSUPPORTED_SOLVER_BACKEND`
- `INVALID_THICKNESS`
- `INVALID_PROCESS_WINDOW`
- `INCONSISTENT_UNITS`
- `CONFORMAL_APPROXIMATION_USED`
- `CONFORMAL_PINCH_OFF_APPROXIMATED`
- `ISOTROPIC_UNDERCUT_APPROXIMATED`
- `TAPERED_PROFILE_APPROXIMATED`
- `CMP_DISHING_HEURISTIC_USED`
- `ETCH_TARGET_EXHAUSTED`
- `ETCH_BLOCKED_BY_NON_TARGET`
- `HIDDEN_MATERIAL_AFFECTS_HEIGHT`
- `GEOMETRY_RESOLUTION`
- `FEATURE_BELOW_GRID_RESOLUTION`
- `RENDER_PROJECTION_INCOMPLETE`
- `STACK_INVARIANT_VIOLATION`

Legacy aliases such as `ISOTROPIC_UNDERCUT`, `TAPERED_PROFILE_APPROXIMATION`,
`CMP_HEURISTIC_USED`, and `CONFORMAL_PINCH_OFF` are still emitted for compatibility.

## Known Correctness Risks

- The sampled backend cannot represent true curved sidewalls or continuous lateral undercut.
- Conformal deposition approximates top/sidewall/bottom growth in sampled columns; seam and
  pinch-off behavior is diagnostic metadata, not full topology.
- Tapered etch currently approximates removal by depth; sidewall angle/CD bias are not rendered as
  polygonal tapered walls.
- CMP uses explicit heuristics for density/dishing/erosion and is not calibrated to pattern
  density physics.
- Process-window variants currently preserve labels and deterministic output but do not yet vary
  individual recipe parameters by lower/target/upper.
- Inline mask intervals can solve without a layout layer reference; the missing layer reference is
  a warning rather than a blocking error.

## Missing Tests

Present tests cover boundary imports, input validation, stack invariants, render projection
validation, strict mode, frame metadata, operation smoke behavior, etch target exhaustion,
non-target etch blockers, and golden solver summaries.

Still missing:

- explicit stop-layer behavior tests for CMP/planarization.
- full JSON snapshot coverage for every requested hard fixture name.
- comparison against pyxs or another independent geometry implementation.

## Recommended Fixes

1. Add process-window parameter substitution before `solve_variants()` returns lower/target/upper.
2. Add polygon-capable render projection shapes before claiming tapered sidewalls are physically
   displayed.
3. Extend golden fixtures to include explicit invalid/failure cases, not only successful summaries.
4. Add a backend conformance test suite that every future `GeometryKernel` implementation must pass.
