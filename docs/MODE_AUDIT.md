# Mode Audit

Last updated: 2026-06-25

## Registry

Modes are declared as `ModeDefinition` records in `domains.modes.mode_registry`, with built-ins assembled by `domains.modes.mode_builtins`, `domains.modes.mode_non_process_builtins`, and `domains.modes.mode_grid_builtin`. External JSON mode loading exists in `domains.modes.mode_loader` and is data-only. Validation exists through `ModeValidator`, including unsupported primitives, unsupported metadata field types, solver operation mismatch, and non-process process-leak checks.

Mode ids persist in `session.session.mode` and hydrate to `SessionRecord.mode`. Invalid saved modes fall back through mode fallback logic and preserve requested mode state in extensions/warnings.

## Built-In Catalog

| mode_id | display_name | family | process-aware | recipe policy | setup stages | capture primitive | metadata fields | measurement policy | artifact policy | editor groups/actions | report sections | status | tests |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| `simple_capture` | Simple Labeled Capture | generic_capture | no | forbidden | default none | site_box | label, notes, capture_role, tags | enabled | site image/capture artifacts | non-process editor | mode reporting defaults | implemented | mode, capture, editor |
| `fast_batch_capture` | Fast Batch Capture | generic_capture | no | forbidden | default none | site_box repeat/no review | label, notes, capture_role, tags | enabled | capture artifacts | non-process editor | mode reporting defaults | implemented | mode/header/batch tests |
| `cad_review` | CAD Review Capture | review | no | forbidden | default none | site_box | label, review_category, severity, notes, tags, owner | enabled | review_annotation | non-process editor | mode reporting defaults | implemented | non-process/editor |
| `optical_metrology` | Optical Metrology | metrology | no | forbidden | origin_choice, optional_origin_point, optional_origin_reference_image, required_optical_alignment_mark, ready_for_capture | site_box, point | label, notes, capture_role, tags | enabled | measurement_annotation | setup editor groups | metrology reports | implemented | setup/non-process |
| `cdsem_capture` | CDSEM Measurement | metrology | no | forbidden | origin_choice, optional_origin_reference_image, required_optical_alignment_mark, required_sem_alignment_mark, ready_for_capture | site_box | label, feature_type, measurement_type, target, lsl, usl, edge_convention, notes | enabled | measurement_annotation | setup editor groups | metrology reports | hidden legacy alias | alias/picker tests |
| `cdsem_measurement` | CDSEM Measurement | metrology | no | forbidden | same as CDSEM capture | site_box | same as CDSEM capture | enabled | measurement_annotation | setup editor groups | metrology reports | implemented | alias/non-process tests |
| `cdsem_planning` | CDSEM Measurement | metrology | no | forbidden | same as CDSEM capture | site_box | same as CDSEM capture | enabled | measurement_annotation | setup editor groups | metrology reports | hidden planning alias | alias/picker tests |
| `grid_measurement` | Grid Measurement | grid | no | forbidden | default none | site_box, grid, measurement | label, notes, row_count, column_count, tags | enabled | site_image, grid_overview, measurement_detail | dashboard, pending, captures, measurements, grid_datasets, overviews, reports, warnings | reporting defaults | implemented_with_scope_limits | grid tests |
| `process_aware_metrology` | Process-Aware Metrology | process_aware | yes | recommended | default none | site_box, measurement | default | enabled | site_image, annotated_image, process_summary | dashboard, setup, pending, captures, process_outputs, warnings | capture_summary, process_summary | hidden internal compatibility mode | process/picker tests |
| `profilometry_planner` | Profilometry Planner | process_aware | yes | recommended | source_layout, coordinate_origin, recipe_context | site_then_line | label, notes, line_label, line_color, line_weight_px, text_scale, target, lsl, usl | enabled | site_image, line_annotation, profile_image, cross_section_image, full_stack_compressed_image | process editor groups/actions | profile_summary, cross_section | implemented | compound/process/render |
| `ellipsometry_planner` | Ellipsometry Planner | process_aware | yes | recommended | source_layout, coordinate_origin, recipe_context | site_then_point | label, point_label, film_target, notes | disabled generic measurement, uses point feature | site_image, point_annotation, stack_image, point_stack_table, film_thickness_summary | process editor groups/actions | point_stack, film_thickness_summary | implemented | compound/process |
| `process_flow_summary` | Process Flow Summary | process_flow | report-only compatibility | forbidden, solver none | default none | default site_box | default | default disabled | default | default | process flow template exists | hidden report-only compatibility mode | render/report/picker tests |
| `fib_cut_planner` | FIB Cut Planner | process_aware | yes | unknown | unknown | intended line/cut | unknown | unknown | FIB render profile exists but no mode | none as mode | FIB package template exists | descoped until complete mode packet | catalog docs |

## Selection Flow

Core creation accepts `NewSessionRequest.mode`, and the session JSON persists that mode. The editor auto-detects mode from an opened session by building adapters and policies from the loaded `SessionRecord.mode`. The KLayout New Session adapter now presents `ModeRegistry.visible_mode_ids()` instead of raw enum values, so hidden compatibility modes can load but are not offered for new sessions.

## Separation Findings

- Non-process built-ins use forbidden recipe policy and `solver_operation = none`.
- Non-process dashboards and metadata tests assert recipe/process context is hidden.
- Process-aware modes expose process context, recipe validation, process-output regeneration, and placeholders.
- `process_flow_summary` is treated as report-only/load-compatible and hidden from new-session picker until a full capture/process workflow is intentionally added.
- `process_aware_metrology` is treated as internal/load-compatible and hidden from new-session picker; explicit product modes are `profilometry_planner` and `ellipsometry_planner`.

## Recommended Actions

1. Keep hidden compatibility modes registered for saved-session loading.
2. Add `fib_cut_planner` only as a complete future mode packet with capture, artifact, editor, and report policies.
3. Add process-flow capture behavior only if it becomes a complete workflow; otherwise keep it report-only and hidden.
4. Keep `cdsem_measurement` as the visible CDSEM mode and `cdsem_capture` / `cdsem_planning` as hidden aliases.
