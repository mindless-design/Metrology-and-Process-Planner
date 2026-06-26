# File Organization Audit

Last updated: 2026-06-25.

## Baseline And Final Verification

Command run before migration:

```text
python -m unittest discover -s tests -t .
```

Result:

```text
Ran 695 tests in 10.792s
FAILED (failures=1, skipped=19)
```

The failure was the existing project quality gate, not a behavior failure:

```text
python\metrology_process_planner\workflows\editor\dispatcher_rendering.py:221: MPP001: file has 256 lines; split it below 220 lines
tests\test_editor_render_bridge.py:34: MPP005: class EditorRenderBridgeTests has 235 lines; split below 140
tests\test_editor_render_bridge.py:181: MPP001: file has 281 lines; split it below 180 lines
```

These size violations were fixed during the migration by splitting editor render target helpers and
render bridge artifact tests.

Final verification after migration:

```text
python -m tools.quality_gates
Quality gates passed.

python -m unittest discover -s tests -t .
Ran 703 tests
OK (skipped=19)

python -m tools.audit_imports
== deprecated_imports ==
OK
== pya_outside_klayout ==
OK
== solver_runtime_imports ==
OK
== domain_runtime_imports ==
OK

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

## Current Source Map

| Path | Classification | Responsibility |
| --- | --- | --- |
| `pymacros/metrology_process_planner_bootstrap.py` | app / KLayout entry | Loads the plugin from KLayout. |
| `python/metrology_process_planner/app/*.py` | app | Command routing, controllers, active session context, modeless window registry, recipe/session/reporting orchestration. |
| `python/metrology_process_planner/domains/*.py` | domain / compatibility | Pure geometry and command records, plus deprecated flat measurement shim retained for compatibility. |
| `python/metrology_process_planner/domains/session/*.py` | domain / session | Session records, serialization, validation, canonical migrations, process-context IO, and process outputs. |
| `python/metrology_process_planner/domains/process/materials.py` | domain / process | Process material records. |
| `python/metrology_process_planner/domains/process/recipe.py` | domain / process | Process recipe aggregate. |
| `python/metrology_process_planner/domains/process/steps.py` | domain / process | Process step records and step enums. |
| `python/metrology_process_planner/domains/process/validation.py` | domain / process | Recipe validation. |
| `python/metrology_process_planner/domains/process/{solver shim files}.py` | compatibility | Deprecated re-export shims to the new `solver` package. |
| `python/metrology_process_planner/domains/artifacts/*.py` | domain / artifacts | Real artifact content, IDs, queries, registry, metadata, visibility, and legacy artifact helpers. |
| `python/metrology_process_planner/domains/capture/*.py` | domain / capture | Real canvas, capture records, capture geometry, capture validation, feature, and grid models. |
| `python/metrology_process_planner/domains/measurement/*.py` | domain / measurement | Real measurement records and validation helpers. |
| `python/metrology_process_planner/domains/modes/*.py` | domain / modes | Real declarative mode loading, registry, validation, built-ins, execution, fallback, and policy modules. |
| `python/metrology_process_planner/domains/warnings/*.py` | domain / warnings | Real warning records and warning visibility helpers. |
| `python/metrology_process_planner/workflows/*.py` | workflow | State transitions for setup, capture, measurement, process context, recipe editor, regeneration, and canvas interactions. |
| `python/metrology_process_planner/workflows/artifacts/*.py` | workflow / artifact repair | Artifact generation, scanning, relinking, repair routing, and visual process artifact handlers. |
| `python/metrology_process_planner/workflows/editor/*.py` | workflow / editor state | Editor document builder, dispatcher, store, render bridge, adapter, and view model construction. |
| `python/metrology_process_planner/persistence/*.py` | persistence | JSON stores, CSV export, session paths, drawing store, recipe store, process output store, schema validation, repair helpers. |
| `python/metrology_process_planner/infrastructure/klayout/*.py` | infrastructure / KLayout | KLayout runtime adapters, plugin registration, crop export, setup/session shells, layout binding, and Qt rasterization under KLayout. |
| `python/metrology_process_planner/infrastructure/{diagnostics shim files}.py` | compatibility | Deprecated re-export shims to the new `diagnostics` package. |
| `python/metrology_process_planner/infrastructure/filesystem/__init__.py` | infrastructure / filesystem | Reserved namespace for file operation adapters. |
| `python/metrology_process_planner/infrastructure/qt/__init__.py` | infrastructure / Qt | Reserved namespace for Qt-specific helpers. |
| `python/metrology_process_planner/diagnostics/*.py` | diagnostics | Diagnostic events, sinks, snapshots, seam checks, trace summaries, exception payloads, and diagnostics service. |
| `python/metrology_process_planner/solver/*.py` | solver | Geometry kernels, process operations, hybrid solver orchestration, solver inputs/results, profiles, invariants, and pyxs compatibility planning. |
| `python/metrology_process_planner/rendering/*.py` | rendering | Render specs, coordinate helpers, export results, and cross-section planning. |
| `python/metrology_process_planner/rendering/cross_section/*.py` | rendering | Cross-section render pipeline, scene models, labels, filtering, projections, and SVG backend. |
| `python/metrology_process_planner/rendering/overview/*.py` | rendering | Overview diagram extraction, layout, labels, leaders, scene IO, and renderer. |
| `python/metrology_process_planner/reporting/*.py` | reporting | Report builder, readiness, themes, manifest, templates, gallery, CSV/PDF/PPTX/image backends. |
| `python/metrology_process_planner/ui/**/*.py` | UI | Widget shells, presenters, view models, session editor, setup guide, recipe editor, diagnostics UI, capture tools, preview widgets, reporting workbench. |
| `python/metrology_process_planner/testing/*.py` | test support | Fixture library and visual regression helpers. |
| `python/metrology_process_planner/devtools/*.py` | developer tooling | Documentation/catalog generation helpers. |
| `python/metrology_process_planner/resources/**` | resources | Package-visible homes for modes, recipes, icons, and report templates. |
| `tests/*.py` | tests | Unit-style regression coverage for domains, workflows, app commands, rendering, reporting, persistence, KLayout adapters, quality gates, and fixtures. |
| `tests/integration/**/*.py` | tests / integration | Dependency direction checks. |
| `tests/unit/architecture/**/*.py` | tests / architecture | Import boundary smoke and layering tests. |
| `tests/fixtures/**` | fixtures | Sessions, recipes, GDS fixtures, and synthetic sessions. |
| `tests/golden/**` | golden | Expected render and overview outputs. |
| `tools/*.py` | tooling | Quality gates, static analysis, package build/release, KLayout runners, UI probes, synthetic/golden generation, and docs generation. |

## Entry Points

- `pymacros/metrology_process_planner_bootstrap.py` is the KLayout bootstrap entry.
- `python/metrology_process_planner/infrastructure/klayout/plugin.py` owns KLayout plugin registration.
- `python/metrology_process_planner/app/bootstrap.py` composes app services and commands.
- `python/metrology_process_planner/app/commands.py` and `python/metrology_process_planner/ui/shell/command_router.py` are command routing hotspots.

## Import Hotspots

- `app/` has many legitimate dependencies because it composes UI, workflows, persistence, diagnostics, reporting, rendering, and infrastructure adapters.
- `workflows/editor/` remains dense, but the migration split the prior size-gate offenders enough for `tools.quality_gates` to pass.
- `domains/process` previously mixed recipe records and solver execution. Solver internals now live under `solver/`; old direct shim modules were removed and are forbidden by `tools.audit_imports`.
- Diagnostics previously lived under `infrastructure/` even though workflows, persistence, app, UI, and tests all consume it. Diagnostics now has its own top-level package.

## KLayout-Specific Files

- `python/metrology_process_planner/infrastructure/klayout/**/*.py`
- `pymacros/metrology_process_planner_bootstrap.py`
- `tools/klayout_runner.py`
- `tools/klayout_ui_runner.py`
- `tools/klayout_ui_robot.py`
- `tools/klayout_probe_scripts.py`
- `tools/klayout_point_probe_scripts.py`
- `tools/klayout_standalone_capture_probe_scripts.py`
- `tests/klayout_*.py`
- `tests/test_klayout_*.py`

## Qt-Specific Files

- `python/metrology_process_planner/infrastructure/klayout/qt_rasterizer.py`
- KLayout shell/widget files under `python/metrology_process_planner/infrastructure/klayout/`
- UI shell and presenter modules under `python/metrology_process_planner/ui/`
- `tests/klayout_widget_fixtures.py`

## Duplicates And Legacy Surfaces

- `domains.process` still re-exports solver symbols lazily for compatibility with existing public imports.
- `domains.process/{solver shim files}.py` are deprecated old direct import paths.
- `infrastructure/diagnostics*.py` and `infrastructure/trace_context.py` are deprecated old diagnostics import paths.
- `domains/session/{artifact,capture,mode,warning shim files}.py` and flat `domains/measurements.py` are deprecated old direct import paths; implementation now lives in the responsibility packages documented in `docs/FILE_MIGRATION_AUDIT.md`.
- Flat compatibility module `domains/geometry.py` remains until callers are migrated to a narrower domain namespace.

## Tests Affected By This Migration

- `tests/unit/architecture/test_import_boundaries.py` guards package import smoke, key forbidden dependencies, old moved-domain import paths, and UI direct session JSON writes.
- `tools/audit_imports.py` now reports old moved-domain imports, `pya` outside KLayout infrastructure, solver runtime leaks, and domain runtime leaks.
- Focused diagnostics tests passed after the diagnostics move.
- Focused solver/rendering tests passed after the solver move.
- `tests/test_editor_render_bridge_artifacts.py` was split out of the oversized render bridge test.
- `python/metrology_process_planner/workflows/editor/dispatcher_artifact_targets.py` was split out of the oversized rendering dispatcher.
- Full tests, quality gates, static analysis, import-linter, project health, compileall, and package build pass through `python -m tools.release_check`.
