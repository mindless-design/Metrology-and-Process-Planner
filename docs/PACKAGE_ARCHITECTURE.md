# Package Architecture

Last updated: 2026-06-25.

## Top-Level Ownership

| Package | Owns | Must not own |
| --- | --- | --- |
| `app` | Plugin/app composition, command IDs, command routing, controller orchestration, active session state, window registry. | Core domain records, direct file format rules, solver math, widget implementation details. |
| `domains` | Pure records, value objects, validation, session/mode/process recipe contracts. | `pya`, Qt bindings, UI widgets, KLayout adapters, report/export backends. |
| `workflows` | State transitions and application-use-case logic over domain records. | Qt widgets, KLayout APIs, direct JSON writes, report rendering backends. |
| `persistence` | Session paths, JSON stores, schema validation, CSV export, recipe/process output stores, atomic persistence concerns. | UI widgets, command routing, KLayout APIs. |
| `infrastructure` | External adapter namespaces, especially KLayout, Qt, filesystem, and project validation adapters. | Pure domain rules or workflow state machines. |
| `diagnostics` | Diagnostic event contracts, sinks, snapshots, seam checks, exception payloads, trace summaries, diagnostics service. | UI presentation and KLayout-specific shell behavior. |
| `solver` | Process solver orchestration, solver inputs/results/profiles, geometry kernels, operations, invariants, pyxs planning. | UI, KLayout, report generation, image drawing. |
| `rendering` | Render intent/specs, cross-section scenes, overview layout, image/export planning. | App command routing, UI widgets, persistence writes. |
| `reporting` | Report documents, readiness, templates, manifests, and export backends. | Transient UI state, KLayout shell state. |
| `ui` | Widget shells, presenters, view models, user-visible command surfaces. | Deep session mutation, direct solver execution, direct file persistence. |
| `resources` | Packaged modes, recipes, icons, and report templates. | Executable Python logic. |
| `testing` | Test-only helpers that are useful across test modules. | Runtime production behavior. |
| `devtools` | Developer documentation/catalog generation helpers. | Runtime plugin behavior. |

## Where New Code Goes

- New command IDs or command dispatch helpers go in `app/`.
- New session, capture, mode, artifact, warning, measurement, or process recipe records go in `domains/`.
- Artifact implementation modules live in `domains/artifacts/`, not under `domains/session/`.
- Capture/canvas implementation modules live in `domains/capture/`, not under `domains/session/`.
- Measurement implementation modules live in `domains/measurement/`, not flat `domains/measurements.py`.
- Declarative mode implementation modules live in `domains/modes/`, not under `domains/session/`.
- Warning implementation modules live in `domains/warnings/`, not under `domains/session/`.
- New workflow state transitions go in `workflows/`.
- New JSON, CSV, or path persistence behavior goes in `persistence/`.
- New KLayout API use goes in `infrastructure/klayout/`.
- New Qt-specific helper code goes in `infrastructure/qt/` or the relevant `ui/` package.
- New filesystem adapter code goes in `infrastructure/filesystem/`.
- New diagnostics contracts, sinks, snapshots, or seam checks go in `diagnostics/`.
- New process solving behavior goes in `solver/`.
- New SVG/image scene planning goes in `rendering/`.
- New report document/export behavior goes in `reporting/`.
- New widget shells, presenters, and view models go in `ui/`.
- New JSON mode/recipe examples, icons, and templates go in `resources/`.

## Dependency Direction

Preferred direction:

```text
app
  -> ui
  -> workflows
  -> persistence
  -> infrastructure
  -> diagnostics
  -> reporting
  -> rendering
  -> solver
  -> domains
```

Lower-level packages should not import upward into app/UI/runtime adapters. Boundary tests in
`tests/unit/architecture/test_import_boundaries.py` enforce the highest-risk parts of this rule.

## KLayout And Qt Boundaries

- `pya` belongs under `infrastructure/klayout/` and the KLayout bootstrap path.
- Qt bindings belong in `ui/`, KLayout shells, or `infrastructure/qt/`.
- `domains`, `solver`, `persistence`, `rendering`, and `reporting` must stay importable without KLayout.

## Compatibility Policy

Compatibility shims are allowed only when they protect a known external or public entrypoint. They
are not allowed merely because internal imports were not updated.

Any retained shim must be:

- Small re-export modules only.
- Quarantined under an approved compatibility location, not scattered through normal architecture
  packages.
- Documented in `docs/COMPATIBILITY_SHIM_AUDIT.md` and `docs/IMPORT_MIGRATION.md`.
- Marked deprecated in their module docstring.
- Covered by package smoke tests.

Current state: no file-level deprecated compatibility shims remain. `tools.audit_imports` forbids
the removed old paths across `python/`, `tests/`, and `tools`.

## Corrective Migration Guardrails

- A package is implemented only when real implementation modules live there.
- New code should import canonical modules directly; see `docs/CANONICAL_IMPORTS.md`.
- Package `__init__.py` files may expose small stable public APIs, but they must not become large
  wildcard re-export surfaces or be the only content of a responsibility package.
- Old paths must be removed unless there is a documented external/public entrypoint reason to keep
  them.
- `python -m tools.audit_imports` checks for deprecated imports, `pya` outside KLayout
  infrastructure, solver runtime leaks, and domain runtime leaks.
