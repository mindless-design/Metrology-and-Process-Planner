# Compatibility Shim Audit

Last updated: 2026-06-25.

## Policy

Compatibility shims are allowed only for known external or public entrypoints. Internal migration
convenience is not enough reason to keep an old import path alive.

Current state:

- No deprecated shim modules remain in normal architecture packages.
- No deprecated internal import users remain in `python/`, `tests/`, or `tools/`.
- `python -m tools.audit_imports` fails on deleted shim paths and reports the canonical replacement
  with file and line number.
- `tests/unit/architecture/test_import_boundaries.py` fails if the removed shim files reappear.

## Removed Shim Inventory

All rows below had `symbols re-exported = all public symbols from canonical target`, no in-repo
internal import users after cleanup, no documented external/public reason to keep, and required
tests `tools.audit_imports`, `tests.unit.architecture.test_import_boundaries`, full unit discovery,
and release check.

| Shim path | Canonical target path | Safe to delete? | Removal action | Status |
| --- | --- | --- | --- | --- |
| `domains/measurements.py` | `domains/measurement/records.py` | yes | deleted, forbidden by audit | `remove_now` |
| `domains/session/artifact_content.py` | `domains/artifacts/artifact_content.py` | yes | deleted, forbidden by audit | `remove_now` |
| `domains/session/artifact_ids.py` | `domains/artifacts/artifact_ids.py` | yes | deleted, forbidden by audit | `remove_now` |
| `domains/session/artifact_query.py` | `domains/artifacts/artifact_query.py` | yes | deleted, forbidden by audit | `remove_now` |
| `domains/session/artifact_refs_metadata.py` | `domains/artifacts/artifact_refs_metadata.py` | yes | deleted, forbidden by audit | `remove_now` |
| `domains/session/artifact_registry.py` | `domains/artifacts/artifact_registry.py` | yes | deleted, forbidden by audit | `remove_now` |
| `domains/session/artifact_repair_metadata.py` | `domains/artifacts/artifact_repair_metadata.py` | yes | deleted, forbidden by audit | `remove_now` |
| `domains/session/artifact_visibility.py` | `domains/artifacts/artifact_visibility.py` | yes | deleted, forbidden by audit | `remove_now` |
| `domains/session/legacy_artifacts.py` | `domains/artifacts/legacy_artifacts.py` | yes | deleted, forbidden by audit | `remove_now` |
| `domains/session/canvas.py` | `domains/capture/canvas.py` | yes | deleted, forbidden by audit | `remove_now` |
| `domains/session/capture_features.py` | `domains/capture/capture_features.py` | yes | deleted, forbidden by audit | `remove_now` |
| `domains/session/capture_geometry.py` | `domains/capture/capture_geometry.py` | yes | deleted, forbidden by audit | `remove_now` |
| `domains/session/capture_geometry_validation.py` | `domains/capture/capture_geometry_validation.py` | yes | deleted, forbidden by audit | `remove_now` |
| `domains/session/captures.py` | `domains/capture/captures.py` | yes | deleted, forbidden by audit | `remove_now` |
| `domains/session/grids.py` | `domains/capture/grids.py` | yes | deleted, forbidden by audit | `remove_now` |
| `domains/session/mode_builtins.py` | `domains/modes/mode_builtins.py` | yes | deleted, forbidden by audit | `remove_now` |
| `domains/session/mode_definition_io.py` | `domains/modes/mode_definition_io.py` | yes | deleted, forbidden by audit | `remove_now` |
| `domains/session/mode_execution.py` | `domains/modes/mode_execution.py` | yes | deleted, forbidden by audit | `remove_now` |
| `domains/session/mode_fallback.py` | `domains/modes/mode_fallback.py` | yes | deleted, forbidden by audit | `remove_now` |
| `domains/session/mode_grid_builtin.py` | `domains/modes/mode_grid_builtin.py` | yes | deleted, forbidden by audit | `remove_now` |
| `domains/session/mode_loader.py` | `domains/modes/mode_loader.py` | yes | deleted, forbidden by audit | `remove_now` |
| `domains/session/mode_non_process_builtins.py` | `domains/modes/mode_non_process_builtins.py` | yes | deleted, forbidden by audit | `remove_now` |
| `domains/session/mode_non_process_support.py` | `domains/modes/mode_non_process_support.py` | yes | deleted, forbidden by audit | `remove_now` |
| `domains/session/mode_non_process_validation.py` | `domains/modes/mode_non_process_validation.py` | yes | deleted, forbidden by audit | `remove_now` |
| `domains/session/mode_output_policies.py` | `domains/modes/mode_output_policies.py` | yes | deleted, forbidden by audit | `remove_now` |
| `domains/session/mode_policies.py` | `domains/modes/mode_policies.py` | yes | deleted, forbidden by audit | `remove_now` |
| `domains/session/mode_process_constants.py` | `domains/modes/mode_process_constants.py` | yes | deleted, forbidden by audit | `remove_now` |
| `domains/session/mode_process_flow.py` | `domains/modes/mode_process_flow.py` | yes | deleted, forbidden by audit | `remove_now` |
| `domains/session/mode_registry.py` | `domains/modes/mode_registry.py` | yes | deleted, forbidden by audit | `remove_now` |
| `domains/session/mode_validation.py` | `domains/modes/mode_validation.py` | yes | deleted, forbidden by audit | `remove_now` |
| `domains/session/warning_visibility.py` | `domains/warnings/warning_visibility.py` | yes | deleted, forbidden by audit | `remove_now` |
| `domains/session/warnings.py` | `domains/warnings/warnings.py` | yes | deleted, forbidden by audit | `remove_now` |
| `domains/process/etch_diagnostics.py` | `solver/etch_diagnostics.py` | yes | deleted, forbidden by audit | `remove_now` |
| `domains/process/etch_operations.py` | `solver/etch_operations.py` | yes | deleted, forbidden by audit | `remove_now` |
| `domains/process/geometry_kernel.py` | `solver/geometry_kernel.py` | yes | deleted, forbidden by audit | `remove_now` |
| `domains/process/geometry_models.py` | `solver/geometry_models.py` | yes | deleted, forbidden by audit | `remove_now` |
| `domains/process/hybrid_diagnostics.py` | `solver/hybrid_diagnostics.py` | yes | deleted, forbidden by audit | `remove_now` |
| `domains/process/hybrid_solver.py` | `solver/hybrid_solver.py` | yes | deleted, forbidden by audit | `remove_now` |
| `domains/process/invariants.py` | `solver/invariants.py` | yes | deleted, forbidden by audit | `remove_now` |
| `domains/process/operation_helpers.py` | `solver/operation_helpers.py` | yes | deleted, forbidden by audit | `remove_now` |
| `domains/process/operation_results.py` | `solver/operation_results.py` | yes | deleted, forbidden by audit | `remove_now` |
| `domains/process/operations.py` | `solver/operations.py` | yes | deleted, forbidden by audit | `remove_now` |
| `domains/process/pyxs_compat.py` | `solver/pyxs_compat.py` | yes | deleted, forbidden by audit | `remove_now` |
| `domains/process/sampled_geometry_helpers.py` | `solver/sampled_geometry_helpers.py` | yes | deleted, forbidden by audit | `remove_now` |
| `domains/process/sampled_geometry_kernel.py` | `solver/sampled_geometry_kernel.py` | yes | deleted, forbidden by audit | `remove_now` |
| `domains/process/solver_models.py` | `solver/solver_models.py` | yes | deleted, forbidden by audit | `remove_now` |
| `domains/process/solver_outputs.py` | `solver/solver_outputs.py` | yes | deleted, forbidden by audit | `remove_now` |
| `domains/process/solver_profiles.py` | `solver/solver_profiles.py` | yes | deleted, forbidden by audit | `remove_now` |
| `domains/process/solver_projection_builders.py` | `solver/solver_projection_builders.py` | yes | deleted, forbidden by audit | `remove_now` |
| `domains/process/solver_result_builders.py` | `solver/solver_result_builders.py` | yes | deleted, forbidden by audit | `remove_now` |
| `domains/process/solver_result_support.py` | `solver/solver_result_support.py` | yes | deleted, forbidden by audit | `remove_now` |
| `domains/process/solver_validation.py` | `solver/solver_validation.py` | yes | deleted, forbidden by audit | `remove_now` |
| `infrastructure/diagnostics.py` | `diagnostics/diagnostics.py` | yes | deleted, forbidden by audit | `remove_now` |
| `infrastructure/diagnostics_assertions.py` | `diagnostics/diagnostics_assertions.py` | yes | deleted, forbidden by audit | `remove_now` |
| `infrastructure/diagnostics_bundle.py` | `diagnostics/diagnostics_bundle.py` | yes | deleted, forbidden by audit | `remove_now` |
| `infrastructure/diagnostics_diffs.py` | `diagnostics/diagnostics_diffs.py` | yes | deleted, forbidden by audit | `remove_now` |
| `infrastructure/diagnostics_exceptions.py` | `diagnostics/diagnostics_exceptions.py` | yes | deleted, forbidden by audit | `remove_now` |
| `infrastructure/diagnostics_models.py` | `diagnostics/diagnostics_models.py` | yes | deleted, forbidden by audit | `remove_now` |
| `infrastructure/diagnostics_project.py` | `diagnostics/diagnostics_project.py` | yes | deleted, forbidden by audit | `remove_now` |
| `infrastructure/diagnostics_seams.py` | `diagnostics/diagnostics_seams.py` | yes | deleted, forbidden by audit | `remove_now` |
| `infrastructure/diagnostics_sinks.py` | `diagnostics/diagnostics_sinks.py` | yes | deleted, forbidden by audit | `remove_now` |
| `infrastructure/diagnostics_snapshots.py` | `diagnostics/diagnostics_snapshots.py` | yes | deleted, forbidden by audit | `remove_now` |
| `infrastructure/diagnostics_timeline.py` | `diagnostics/diagnostics_timeline.py` | yes | deleted, forbidden by audit | `remove_now` |
| `infrastructure/trace_context.py` | `diagnostics/trace_context.py` | yes | deleted, forbidden by audit | `remove_now` |

## Retained Compatibility

No file-level deprecated shim modules are retained. Package-level stable public APIs such as
`domains.session`, `domains.process`, `diagnostics`, and `solver` remain as intentionally documented
package APIs, not old-path shim files. New code should prefer the canonical modules listed in
`docs/CANONICAL_IMPORTS.md`.
