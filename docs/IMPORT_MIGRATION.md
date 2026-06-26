# Import Migration

Last updated: 2026-06-25.

## Current State

Deprecated file-level compatibility shims have been removed from normal architecture packages.
Internal code in `python/`, `tests/`, and `tools/` must import canonical modules directly.

Use:

```text
python -m tools.audit_imports
```

The audit fails on deleted shim imports, prints file and line number, and suggests the canonical
replacement.

## Removed Shim Paths

| Old import path family | New canonical import family | Shim removed? | Remaining users |
| --- | --- | --- | --- |
| `metrology_process_planner.domains.measurements` | `metrology_process_planner.domains.measurement.records` | yes | none |
| `metrology_process_planner.domains.session.artifact_*` | `metrology_process_planner.domains.artifacts.*` | yes | none |
| `metrology_process_planner.domains.session.legacy_artifacts` | `metrology_process_planner.domains.artifacts.legacy_artifacts` | yes | none |
| `metrology_process_planner.domains.session.canvas` | `metrology_process_planner.domains.capture.canvas` | yes | none |
| `metrology_process_planner.domains.session.capture_*` | `metrology_process_planner.domains.capture.*` | yes | none |
| `metrology_process_planner.domains.session.captures` | `metrology_process_planner.domains.capture.captures` | yes | none |
| `metrology_process_planner.domains.session.grids` | `metrology_process_planner.domains.capture.grids` | yes | none |
| `metrology_process_planner.domains.session.mode_*` | `metrology_process_planner.domains.modes.*` | yes | none |
| `metrology_process_planner.domains.session.warning*` | `metrology_process_planner.domains.warnings.*` | yes | none |
| `metrology_process_planner.domains.process.<solver module>` | `metrology_process_planner.solver.<solver module>` | yes | none |
| `metrology_process_planner.infrastructure.diagnostics*` | `metrology_process_planner.diagnostics.*` | yes | none |
| `metrology_process_planner.infrastructure.trace_context` | `metrology_process_planner.diagnostics.trace_context` | yes | none |

The complete per-file inventory is in `docs/COMPATIBILITY_SHIM_AUDIT.md`.

## Stable Package APIs

Package-level APIs such as `metrology_process_planner.domains.session`,
`metrology_process_planner.domains.process`, `metrology_process_planner.diagnostics`, and
`metrology_process_planner.solver` remain supported public package APIs. They are not file-level
compatibility shims, but new internal code should prefer the canonical module paths documented in
`docs/CANONICAL_IMPORTS.md`.
