# Dependency Audit

Last updated: 2026-06-25

## Expected Direction

- `ui` depends on view models and commands.
- `app` owns command routing, modeless controllers, and KLayout/product surface orchestration.
- `workflows` depend on domain models, rendering/reporting services, persistence abstractions, and
  service-level contracts.
- `domains` depend on pure Python models only.
- `persistence` depends on domain/session models.
- `infrastructure.klayout` adapts KLayout and Qt to app/workflow interfaces.
- `rendering` depends on solver/render models, not UI.
- `reporting` depends on session/artifact/report models, not live UI.
- `diagnostics` reads through service-level snapshots and command traces.

## Automated Checks

- `pyproject.toml` import-linter contracts forbid domain/workflow/persistence/rendering imports of
  `app`, `ui`, `infrastructure.klayout`, and `pya`.
- `tests/integration/dependency/test_dependency_direction.py` now AST-scans core packages for the
  same forbidden edges.

Current evidence:

- `lint-imports`: passed after this audit.
- `python -m pytest tests/integration/dependency/test_dependency_direction.py`: passed.
- `python -m tools.release_check --include-klayout`: passed after this audit.

## Finding Fixed

The audit found `workflows.recipe_editor_*` modules importing `metrology_process_planner.app`
command types and normalization helpers. This made recipe workflow results depend on app-layer
types.

Fix:

- Added `metrology_process_planner.domains.commands.CommandId`.
- Moved `command_id_from_view_action()` to the same pure module.
- Re-exported `CommandId` through `app.command_types` and `app.commands` for existing app/tests.
- Updated recipe workflow modules to import the pure command contract.

## Static Analysis Result

`python -m tools.static_analysis --fail-on-missing` passes through the release check. The broader
lane now covers Ruff, mypy, xenon, radon, interrogate, import-linter, vulture, and coverage.

## No Critical Forbidden Edges Found

- No domain imports of `pya`/Qt/app/UI were found.
- Solver modules do not import `pya` or Qt.
- Rendering modules do not import session editor widgets.
- Reporting modules consume report/session/artifact models rather than live UI state.
