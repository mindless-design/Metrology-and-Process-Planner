# Solver Render Contract

Last updated: 2026-06-24

## Contract Flow

`ProcessRecipe + geometry/request metadata -> SolverInput -> GeometryKernel backend ->
SolverResult -> RenderProjection / ProcessFrame / samples / diagnostics -> renderer`

Renderer code must consume public process-domain records. It must not query private solver helpers
or infer material identity from recipe steps.

## SolverInput

Required fields or equivalents:

- `recipe`
- `options`
- `geometry_context`
- `requested_outputs`
- `units`
- `variant_selection`
- `source_geometry_metadata`
- `backend_id`

Supported geometry forms:

- `GeometrySnapshot`
- `CutlineSample`
- `PointSample`
- `MaskInterval`

`validate_solver_input()` returns structured diagnostics for missing recipe data, invalid
thickness, invalid process windows, unsupported backend IDs, inconsistent units, empty mask
intervals, and unresolved material/layer references.

## SolverResult

Renderer-ready result fields:

- `solver_id`
- `backend_id`
- `backend_version`
- `input_hash`
- `recipe_id`
- `variant_label`
- `final_stack`
- `point_samples`
- `cutline_samples`
- `frames`
- `render_projections`
- `diagnostics`
- `approximation_notes`
- `metrics`
- `units`
- `material_metadata`

The result is deterministic for identical recipe/options/backend/unit input. `input_hash` is a
stable SHA-256 over recipe JSON, solver options representation, units, variant selection, and
backend ID.

## RenderProjection

Projection fields:

- `projection_id`
- `projection_type`
- `source_solver_result_id`
- `source_step_id`
- `source_capture_id`
- `materials`
- `regions`
- `surface`
- `material_order`
- `physical_bounds`
- `units`
- `hidden_material_ids`
- `label_candidates`
- `changed_regions`
- `warnings`
- `compression_hints`
- `thin_layer_hints`
- `approximation_notes`

Projection types:

- `physical_cross_section`
- `illustrative_cross_section`
- `profilometry_surface`
- `fib_full_stack`
- `process_flow_frame`
- `point_stack`

Current sampled projections are region/interval based. Future polygonal or layered projections
should extend the public model rather than requiring renderer access to private backend data.

## ProcessFrame

Frame fields:

- `frame_id`
- `step_index`
- `step_id`
- `step_name`
- `operation_type`
- `stack_signature`
- `changed_from_previous`
- `changed_regions`
- `projection` / `render_projection`
- `diagnostics`
- `variant_label`

Current compatibility behavior keeps `frame_every_step=True` as the default. Frames include
`changed_from_previous` so process-flow renderers can filter unchanged frames deterministically.
`emit_unchanged_frames` remains available for explicit debug-style workflows.

## Validation

Use `validate_render_projection(projection)` before sending solver output into a renderer that
cannot tolerate incomplete geometry.

Checks:

- projection type is supported.
- material IDs resolve.
- geometry is non-empty unless intentionally empty diagnostics are attached.
- units are present.
- physical bounds are valid.
- region bounds are valid.

Strict mode runs projection validation for final projections and stack invariant checks after each
solver step.
