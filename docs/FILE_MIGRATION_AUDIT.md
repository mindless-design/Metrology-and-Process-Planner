# File Migration Audit

Last updated: 2026-06-25.

## Baseline

Before this corrective migration:

```text
python -m unittest discover -s tests -t .
Ran 699 tests
OK (skipped=19)
```

The prior package tree had several packages that were only `__init__.py` facade wrappers:

| Package | Fake migration issue | Current state |
| --- | --- | --- |
| `domains/artifacts` | `__init__.py` re-exported implementation from `domains/session/artifact_*`. | Real artifact modules now live in `domains/artifacts`. |
| `domains/capture` | `__init__.py` re-exported implementation from `domains/session/canvas.py`, `capture_*.py`, `captures.py`. | Real capture/canvas modules now live in `domains/capture`. |
| `domains/measurement` | `__init__.py` re-exported implementation from flat `domains/measurements.py`. | Real measurement record module now lives in `domains/measurement/records.py`. |
| `domains/modes` | `__init__.py` re-exported implementation from `domains/session/mode_*.py`. | Real mode modules now live in `domains/modes`. |
| `domains/warnings` | `__init__.py` re-exported implementation from `domains/session/warnings.py` and `warning_visibility.py`. | Real warning modules now live in `domains/warnings`. |
| `infrastructure/filesystem` | Placeholder package only. | Still a reserved namespace; no implementation moved there yet. |
| `infrastructure/qt` | Placeholder package only. | Still a reserved namespace; no implementation moved there yet. |

## Migration Inventory

| Old file path | Current actual implementation location | Intended new package | Physically moved? | Old path still owns implementation? | New path only re-exports? | Tests covering import | Migration status |
| --- | --- | --- | --- | --- | --- | --- | --- |
| `domains/session/artifact_content.py` | `domains/artifacts/artifact_content.py` | `domain_artifacts` | yes | no | no | `tests/unit/architecture/test_import_boundaries.py`, `tools/audit_imports.py` | `moved_and_imports_updated` |
| `domains/session/artifact_ids.py` | `domains/artifacts/artifact_ids.py` | `domain_artifacts` | yes | no | no | architecture import audit | `moved_and_imports_updated` |
| `domains/session/artifact_query.py` | `domains/artifacts/artifact_query.py` | `domain_artifacts` | yes | no | no | architecture import audit | `moved_and_imports_updated` |
| `domains/session/artifact_refs_metadata.py` | `domains/artifacts/artifact_refs_metadata.py` | `domain_artifacts` | yes | no | no | architecture import audit | `moved_and_imports_updated` |
| `domains/session/artifact_registry.py` | `domains/artifacts/artifact_registry.py` | `domain_artifacts` | yes | no | no | `tests/test_artifact_lifecycle.py`, architecture import audit | `moved_and_imports_updated` |
| `domains/session/artifact_repair_metadata.py` | `domains/artifacts/artifact_repair_metadata.py` | `domain_artifacts` | yes | no | no | architecture import audit | `moved_and_imports_updated` |
| `domains/session/artifact_visibility.py` | `domains/artifacts/artifact_visibility.py` | `domain_artifacts` | yes | no | no | architecture import audit | `moved_and_imports_updated` |
| `domains/session/legacy_artifacts.py` | `domains/artifacts/legacy_artifacts.py` | `domain_artifacts` | yes | no | no | architecture import audit | `moved_and_imports_updated` |
| `domains/session/canvas.py` | `domains/capture/canvas.py` | `domain_capture` | yes | no | no | architecture import audit | `moved_and_imports_updated` |
| `domains/session/capture_features.py` | `domains/capture/capture_features.py` | `domain_capture` | yes | no | no | architecture import audit | `moved_and_imports_updated` |
| `domains/session/capture_geometry.py` | `domains/capture/capture_geometry.py` | `domain_capture` | yes | no | no | `tests/test_session_round_trip.py`, architecture import audit | `moved_and_imports_updated` |
| `domains/session/capture_geometry_validation.py` | `domains/capture/capture_geometry_validation.py` | `domain_capture` | yes | no | no | architecture import audit | `moved_and_imports_updated` |
| `domains/session/captures.py` | `domains/capture/captures.py` | `domain_capture` | yes | no | no | `tests/test_session_round_trip.py`, architecture import audit | `moved_and_imports_updated` |
| `domains/session/grids.py` | `domains/capture/grids.py` | `domain_capture` | yes | no | no | architecture import audit | `moved_and_imports_updated` |
| `domains/measurements.py` | `domains/measurement/records.py` | `domain_measurement` | yes | no | no | `tests/test_measurement_validation.py`, architecture import audit | `moved_and_imports_updated` |
| `domains/session/mode_builtins.py` | `domains/modes/mode_builtins.py` | `domain_modes` | yes | no | no | `tests/test_mode_registry.py`, architecture import audit | `moved_and_imports_updated` |
| `domains/session/mode_definition_io.py` | `domains/modes/mode_definition_io.py` | `domain_modes` | yes | no | no | `tests/test_mode_registry.py`, architecture import audit | `moved_and_imports_updated` |
| `domains/session/mode_execution.py` | `domains/modes/mode_execution.py` | `domain_modes` | yes | no | no | `tests/test_mode_registry.py`, architecture import audit | `moved_and_imports_updated` |
| `domains/session/mode_fallback.py` | `domains/modes/mode_fallback.py` | `domain_modes` | yes | no | no | architecture import audit | `moved_and_imports_updated` |
| `domains/session/mode_grid_builtin.py` | `domains/modes/mode_grid_builtin.py` | `domain_modes` | yes | no | no | `tests/test_mode_registry.py`, architecture import audit | `moved_and_imports_updated` |
| `domains/session/mode_loader.py` | `domains/modes/mode_loader.py` | `domain_modes` | yes | no | no | `tests/test_mode_registry.py`, architecture import audit | `moved_and_imports_updated` |
| `domains/session/mode_non_process_builtins.py` | `domains/modes/mode_non_process_builtins.py` | `domain_modes` | yes | no | no | `tests/test_mode_registry.py`, architecture import audit | `moved_and_imports_updated` |
| `domains/session/mode_non_process_support.py` | `domains/modes/mode_non_process_support.py` | `domain_modes` | yes | no | no | `tests/test_mode_registry.py`, architecture import audit | `moved_and_imports_updated` |
| `domains/session/mode_non_process_validation.py` | `domains/modes/mode_non_process_validation.py` | `domain_modes` | yes | no | no | `tests/test_mode_registry.py`, architecture import audit | `moved_and_imports_updated` |
| `domains/session/mode_output_policies.py` | `domains/modes/mode_output_policies.py` | `domain_modes` | yes | no | no | `tests/test_mode_registry.py`, architecture import audit | `moved_and_imports_updated` |
| `domains/session/mode_policies.py` | `domains/modes/mode_policies.py` | `domain_modes` | yes | no | no | `tests/test_mode_registry.py`, architecture import audit | `moved_and_imports_updated` |
| `domains/session/mode_process_constants.py` | `domains/modes/mode_process_constants.py` | `domain_modes` | yes | no | no | architecture import audit | `moved_and_imports_updated` |
| `domains/session/mode_process_flow.py` | `domains/modes/mode_process_flow.py` | `domain_modes` | yes | no | no | `tests/test_mode_registry.py`, architecture import audit | `moved_and_imports_updated` |
| `domains/session/mode_registry.py` | `domains/modes/mode_registry.py` | `domain_modes` | yes | no | no | `tests/test_mode_registry.py`, architecture import audit | `moved_and_imports_updated` |
| `domains/session/mode_validation.py` | `domains/modes/mode_validation.py` | `domain_modes` | yes | no | no | `tests/test_mode_registry.py`, architecture import audit | `moved_and_imports_updated` |
| `domains/session/warnings.py` | `domains/warnings/warnings.py` | `domain_warnings` | yes | no | no | architecture import audit | `moved_and_imports_updated` |
| `domains/session/warning_visibility.py` | `domains/warnings/warning_visibility.py` | `domain_warnings` | yes | no | no | architecture import audit | `moved_and_imports_updated` |

## Compatibility Shims

Old files listed above were removed in the compatibility cleanup. The canonical implementations live
in the new responsibility packages and the old import paths are forbidden by `tools.audit_imports`.

The old solver shims in `domains/process/{solver modules}.py` and old diagnostics shims in
`infrastructure/diagnostics*.py` were also removed; see `docs/COMPATIBILITY_SHIM_AUDIT.md`.

## Current Audit Tool Evidence

```text
python -m tools.audit_imports
== deprecated_imports ==
OK
== pya_outside_klayout ==
OK
== solver_runtime_imports ==
OK
== domain_runtime_imports ==
OK
```

## Final Verification

```text
python -m tools.quality_gates
Quality gates passed.

python -m tools.audit_imports
== deprecated_imports ==
OK
== pya_outside_klayout ==
OK
== solver_runtime_imports ==
OK
== domain_runtime_imports ==
OK

python -m unittest discover -s tests -t .
Ran 703 tests
OK (skipped=19)

python -m tools.release_check
Quality gates passed.
All checks passed!
Success: no issues found in 491 source files
Import Linter: 2 kept, 0 broken
Overall Health: 100%
Ran 703 tests
OK (skipped=19)
Built package: dist\metrology_process_planner.zip

python -m tools.release_check --include-klayout
Quality gates passed.
All checks passed!
Success: no issues found in 491 source files
Import Linter: 2 kept, 0 broken
Overall Health: 100%
Ran 703 tests
OK (skipped=19)
Ran 10 KLayout integration tests
OK
Ran 5 KLayout process regression tests
OK
Ran 4 KLayout UI automation tests
OK
Built package: dist\metrology_process_planner.zip
```
