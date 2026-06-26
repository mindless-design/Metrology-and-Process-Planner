# Architecture Contracts To Protect

Last updated: 2026-06-25

These contracts are non-negotiable during stabilization. A fix that violates one of these contracts is not a valid fix, even if a narrow workflow appears to work.

## Contract 1: Session JSON Is The Durable Document

Why it matters: Saved product state must survive restart, reload, repair, reporting, and diagnostics.

Violations look like:

- writing canonical state only to widgets, CSV, images, or temp files
- storing captures only in overlays
- storing measurements globally or outside parent captures
- writing session JSON outside session/document stores

Where to test/check:

- `tests/test_session_document_lifecycle.py`
- `tests/test_canonical_session_json.py`
- `tests/test_session_round_trip.py`
- `docs/NO_BYPASS_AUDIT.md`
- import and IO audits for direct session writes

## Contract 2: `SessionDocument` Wraps The Active Editable Session

Why it matters: The editor, diagnostics, reporting, and commands need one coherent in-memory document with dirty state, selection, loaded path, and normalized item indexes.

Violations look like:

- UI widgets mutating raw session dicts
- commands bypassing `SessionEditorController` or document store
- separate active-session objects drifting from editor document state

Where to test/check:

- `tests/test_session_editor_store_dispatcher.py`
- `tests/test_session_editor_shell_controller.py`
- `tests/test_session_editor_command_bridge.py`
- `docs/INTEGRATION_SEAMS.md`

## Contract 3: UI Emits Commands; Workflows Mutate State

Why it matters: Command routing gives diagnostics, blocked/unavailable states, and shared behavior across menu, editor, setup guide, and workbench surfaces.

Violations look like:

- widget callbacks editing `SessionRecord` fields directly
- UI invoking solver, renderer, or artifact repair directly
- mode-specific buttons implementing workflow logic

Where to test/check:

- `tests/test_command_registry.py`
- `tests/test_session_editor_command_bridge.py`
- `tests/test_setup_guide_commands.py`
- `tests/test_diagnostics_actions.py`

## Contract 4: Modes Configure Workflows; Modes Do Not Implement Workflows

Why it matters: Adding a mode should not fork capture, setup, editor, reporting, or process logic.

Violations look like:

- mode-specific capture handlers
- mode-specific review dialogs for normal capture/measurement
- hard-coded built-in mode ids where policy data should be used

Where to test/check:

- `tests/test_mode_registry.py`
- `tests/test_mode_validation.py`
- `tests/test_compound_mode_routing.py`
- `tests/test_non_process_mode_hardening.py`

## Contract 5: Canvas Overlays Are Visual Proxies, Not Canonical State

Why it matters: KLayout overlay state is ephemeral. The durable source is `CanvasObject`, captures, measurements, and feature records in session JSON.

Violations look like:

- treating KLayout marker objects as saved state
- mutating source layout geometry for overlays
- failing to restore overlays from session records after reload

Where to test/check:

- `tests/test_canvas_overlays_and_selection.py`
- `tests/test_canvas_session_models.py`
- `tests/test_klayout_boundary.py`
- live Bind Current Layout tests to add

## Contract 6: Artifacts Are Derived And Centrally Registered

Why it matters: Repair, reporting, stale detection, diagnostics, and export readiness require one central artifact registry.

Violations look like:

- raw filenames stored only on captures
- generated files without `ArtifactRecord`
- repair actions editing owner refs without central registry updates
- report outputs not registered back into session artifacts

Where to test/check:

- `tests/test_artifact_lifecycle.py`
- `tests/test_artifact_repair_service.py`
- `tests/test_session_editor_csv_export_artifacts.py`
- `tests/test_reporting_pipeline.py`

## Contract 7: Warnings Are Structured Records

Why it matters: Users need actionable repair guidance and diagnostics need stable codes.

Violations look like:

- plain string errors hidden in UI text only
- exceptions escaping command boundaries
- deleting warning history instead of marking resolved/ignored where appropriate

Where to test/check:

- `tests/test_warning_repair_actions.py`
- `tests/test_exception_diagnostics.py`
- `tests/test_diagnostics_pipeline.py`

## Contract 8: Solver Core Does Not Import KLayout, Qt, App, Or UI

Why it matters: Solver behavior must be testable headlessly and reusable by reports/renderers.

Violations look like:

- imports of `pya`, Qt, `app`, or `ui` in `domains.process`
- solver calling render/export/UI code
- UI passing private widget state into solver

Where to test/check:

- `tests/test_solver_contract.py`
- `tests/integration/dependency/test_dependency_direction.py`
- `lint-imports`
- `python -m tools.release_check --include-klayout`

## Contract 9: Renderer Consumes Render Contracts, Not Solver Internals

Why it matters: Renderers should depend on `RenderProjection`, `RenderIntent`, and scene models, not private solver implementation details.

Violations look like:

- renderer reaching into solver kernels or process-step execution internals
- solver special-casing renderer backends
- render failures corrupting process output records

Where to test/check:

- `tests/test_solver_contract.py`
- `tests/test_cross_section_rendering_pipeline.py`
- `tests/test_synthetic_render_regression.py`
- `docs/RENDERING_AUDIT.md`

## Contract 10: Reports Consume `SessionDocument` And Artifact Registry, Not Live UI State

Why it matters: Reports must be reproducible from saved session JSON and artifacts.

Violations look like:

- report builder reading active widgets
- report output depending on KLayout current view when artifacts already exist
- report files written without manifest/artifact records

Where to test/check:

- `tests/test_reporting_pipeline.py`
- `tests/test_reporting_readiness.py`
- `tests/test_reporting_workbench.py`
- `tests/test_reporting_output_quality.py`

## Contract 11: Diagnostics Inspect Public Service State

Why it matters: Diagnostics should remain safe and non-invasive.

Violations look like:

- diagnostics reading private widget internals
- diagnostics mutating product state except through explicit actions
- diagnostic actions bypassing command/workflow services

Where to test/check:

- `tests/test_diagnostics_visibility.py`
- `tests/test_diagnostics_actions.py`
- `tests/test_diagnostics_pipeline.py`
- `python/metrology_process_planner/app/diagnostics_summary.py`

## Contract 12: Dependency Direction Stays Enforced

Why it matters: The repo is intentionally avoiding a large tangled plugin. Dependency direction is how the architecture stays understandable.

Violations look like:

- domains importing app/UI/KLayout
- workflows importing app controllers
- persistence importing UI
- rendering/reporting importing live UI widgets

Where to test/check:

- `tests/integration/dependency/test_dependency_direction.py`
- `lint-imports`
- `tools/static_analysis.py`
- `tools/quality_gates.py`
