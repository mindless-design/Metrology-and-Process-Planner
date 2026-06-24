# Metrology and Process Planner

A Python-first KLayout plugin for repeatable layout capture, metrology planning,
process-stack visualization, and restartable reporting.

This repository is intentionally shaped so that most behavior can be tested
without KLayout:

- `python/metrology_process_planner/domains`: pure data models and validation.
- `python/metrology_process_planner/domains`: pure data models and validation.
- `python/metrology_process_planner/workflows`: explicit state machines and user intents.
- `python/metrology_process_planner/persistence`: JSON/CSV/session-folder IO.
- `python/metrology_process_planner/rendering`: render specs and export contracts.
- `python/metrology_process_planner/infrastructure/klayout`: thin KLayout adapters.
- `python/metrology_process_planner/app`: composition, command routing, plugin entrypoints.
- `pymacros`: KLayout-discovered bootstrap macros.
- `grain.xml`: Salt package metadata at the KLayout package root.

## Local Development

Use Python 3.9 or newer. The core package has no runtime dependency on KLayout.

```powershell
python -m unittest discover -s tests -t .
```

Run maintainability gates directly:

```powershell
python -m tools.quality_gates
```

Run optional third-party analysis:

```powershell
python -m tools.static_analysis
```

Run the local release check:

```powershell
python -m tools.release_check
```

Run real KLayout integration tests:

```powershell
$env:MPP_RUN_KLAYOUT_TESTS = "1"
python -m unittest tests.test_klayout_integration
$env:MPP_RUN_KLAYOUT_UI_TESTS = "1"
python -m unittest tests.test_klayout_ui_automation
```

Optional developer tools are listed in `pyproject.toml`:

```powershell
python -m pip install -e ".[dev]"
python -m pytest
python -m tools.static_analysis --fail-on-missing
python -m ruff check .
python -m mypy python
```

## Design Rules

1. KLayout and Qt integration stays in `infrastructure/klayout` and `ui`.
2. Pure domain logic must not import `pya`, Qt, or live application state.
3. Sessions are durable data, not UI memory.
4. Workflows return explicit user intents and events.
5. Export/report tools load from saved session artifacts whenever possible.
6. Missing artifacts are diagnostics to surface and repair, not silent failures.

See `docs/architecture.md` and `docs/coding-guidelines.md` before adding large
features. The enforceable budgets are documented in `docs/quality-gates.md`, and
optional analyzer behavior is documented in `docs/static-analysis.md`.
KLayout package structure is documented in `docs/klayout-package-guidelines.md`.
KLayout test automation is documented in `docs/klayout-ui-testing.md`.
Release packaging is documented in `docs/release-pipeline.md`.
