# Agent Work Packets

Last updated: 2026-06-25

Status: historical execution packet list. The P0/P1/P2/P3 stabilization packets below have been implemented or explicitly descoped where noted in `docs/NEXT_PRIORITIES.md` and `docs/IMPLEMENTATION_STATUS.md`.

Each packet is sized for one agent to complete without constant supervision. For current next work, use `docs/NEXT_PRIORITIES.md` and `docs/STABILIZATION_COMPLETION_AUDIT.md`.

## Packet 1: Wire Session Document Lifecycle UI Adapters

Priority: P0

Goal: Make New Session, Open Session, Open Recent, and Save As usable from the product UI by supplying path, folder, mode, and destination inputs to existing lifecycle methods.

Why: The core document lifecycle exists, but normal operator entrypoints still return unavailable when they need user-selected paths.

Scope:

- KLayout/Qt picker abstraction for folder/file/destination/mode.
- Command handlers for `NEW_SESSION`, `OPEN_SESSION`, `OPEN_RECENT_SESSION`, `SAVE_SESSION_AS`.
- Active document/context/recent session updates.
- Cancel and invalid-path command results.

Out of scope:

- Redesigning session JSON.
- Adding new capture modes.
- Polishing the entire editor shell.

Relevant docs:

- `docs/STABILIZATION_ROADMAP.md`
- `docs/P0_BLOCKERS.md`
- `docs/SESSION_DOCUMENT_AUDIT.md`
- `docs/UI_AUDIT.md`
- `docs/ARCHITECTURE_CONTRACTS_TO_PROTECT.md`

Likely files/modules:

- `python/metrology_process_planner/app/session_document_commands.py`
- `python/metrology_process_planner/app/session_editor_lifecycle.py`
- `python/metrology_process_planner/app/session_editor_surface.py`
- `python/metrology_process_planner/ui/session_editor/*`
- `python/metrology_process_planner/infrastructure/klayout/plugin.py`

Tasks:

1. Add a picker/input boundary that is fakeable in tests.
2. Route New Session to `SessionEditorController.new_session(...)`.
3. Route Open Session to `open_session_path(...)`.
4. Route Open Recent to selected recent path.
5. Route Save As to `save_current_session_as(...)`.
6. Preserve `CommandRouteResult` semantics for success, cancel, unavailable, blocked, and error.
7. Refresh current editor window and active context after successful commands.

Tests:

- `test_new_session_menu_uses_folder_label_and_mode_picker`
- `test_open_session_menu_loads_selected_session_json`
- `test_open_recent_menu_loads_recent_path`
- `test_save_as_menu_writes_destination_and_updates_loaded_path`
- `test_path_picker_cancel_is_non_mutating`

Acceptance criteria:

- User can create, open, reopen recent, and Save As from UI.
- Normal supplied-input flows do not return unavailable.
- Active `SessionDocument` and path state are correct.
- Tests pass without requiring live KLayout except designated smoke tests.

Stop conditions:

- Existing lifecycle methods cannot represent required UI state.
- Feature matrix contradicts current code after inspection.
- Repository cannot import.

Dependencies: none.

## Packet 2: Bind Current Layout And Restore Overlays

Priority: P0

Goal: Implement `Bind Current Layout to Session` so a live KLayout view can be associated with the active session and saved overlays can be restored from session JSON.

Why: Source layout binding and live overlay restore are the highest-risk remaining persistence seam.

Scope:

- KLayout adapter for current layout metadata.
- Command handler for binding current layout.
- Update `SourceLayoutContext` on the active `SessionDocument`.
- Overlay restore from durable `CanvasObject` records.
- Diagnostics rows/warnings for bound layout and mismatch.

Out of scope:

- Mutating KLayout layout geometry.
- Replacing canvas object persistence.
- Implementing layout crop generator unless needed for a smoke fixture.

Relevant docs:

- `docs/P0_BLOCKERS.md`
- `docs/INTEGRATION_SEAMS.md`
- `docs/CONTRACT_MATRIX.md`
- `docs/TEST_PLAN_NEXT.md`

Likely files/modules:

- `python/metrology_process_planner/app/session_document_commands.py`
- `python/metrology_process_planner/infrastructure/klayout/geometry.py`
- `python/metrology_process_planner/infrastructure/klayout/overlays.py`
- `python/metrology_process_planner/workflows/overlays.py`
- `python/metrology_process_planner/app/diagnostics_summary.py`

Tasks:

1. Define fakeable KLayout current-layout metadata provider.
2. Implement bind command and session document replacement.
3. Add mismatch warnings for incompatible layout/fingerprint.
4. Restore saved overlay commands through overlay manager.
5. Add diagnostics summary rows for bound layout/overlay restore.
6. Add unit and live KLayout smoke coverage.

Tests:

- `test_bind_current_layout_updates_source_layout_context`
- `test_bind_current_layout_restores_canvas_overlays`
- `test_bind_current_layout_mismatch_adds_warning`
- live KLayout bind smoke

Acceptance criteria:

- Bound layout metadata persists in session JSON.
- Saved overlays restore after reopen/bind.
- Mismatch is visible and repairable.
- KLayout source geometry is not mutated.

Stop conditions:

- KLayout API cannot expose required layout/view metadata.
- Live KLayout test lane is unavailable after three attempts; continue with fakeable adapter and document live-test gap.

Dependencies: Packet 1 is strongly preferred but not strictly required for unit work.

## Packet 3: Stabilize Production Session Editor Shell

Priority: P1

Goal: Build the production Qt shell for the existing unified editor view-model contract.

Why: The document model is strong, but users need a real operator surface for review, repair, save, and reporting handoffs.

Scope:

- Header/session bar.
- Left navigator.
- Center preview/details.
- Right inspector/actions.
- Bottom status/warning strip.
- Generic pending simple/composite/measurement review actions.
- Dirty-state prompt rendering.

Out of scope:

- Mode-specific review dialogs.
- New product features.
- Replacing `SessionDocument`.

Relevant docs:

- `docs/UI_AUDIT.md`
- `docs/ARCHITECTURE_CONTRACTS_TO_PROTECT.md`
- `docs/P1_INTEGRATION_FIXES.md`

Likely files/modules:

- `python/metrology_process_planner/ui/session_editor/*`
- `python/metrology_process_planner/app/session_editor_surface.py`
- `python/metrology_process_planner/workflows/editor/*`

Tasks:

1. Inspect existing shell contract and fake backend.
2. Implement Qt widget backend that consumes current view models.
3. Wire action callbacks through existing router/dispatcher.
4. Render disabled reasons and status/warning strip.
5. Add structural and screenshot/visual smoke tests where feasible.

Tests:

- `test_qt_session_editor_renders_document_regions`
- `test_qt_session_editor_routes_actions_through_command_router`
- `test_qt_session_editor_dirty_close_prompt`
- `test_qt_pending_reviews_render_inside_unified_editor`

Acceptance criteria:

- Editor shell never reads raw JSON directly.
- All normal review actions stay inside unified editor.
- Dirty/pending blockers are visible.
- Existing editor tests continue passing.

Stop conditions:

- Qt runtime is unavailable for production shell tests; implement fakeable backend tests and document live UI gap.

Dependencies: Packet 1.

## Packet 4: Implement High-Value Artifact Generators

Priority: P1

Goal: Convert the most important artifact generator declarations into working handlers.

Why: Artifact repair cannot be trusted if missing/stale records have no concrete regeneration path.

Scope:

- remaining cross-section/profile visual render artifacts
- explicit unavailable policies for visual declarations that are not yet product-ready
- regression coverage that keeps existing measurement annotation, overview, process-output JSON,
  PowerPoint report-output, and KLayout-injected live layout crop repair working

Out of scope:

- New report templates.
- Manual image editing.
- Rewriting artifact registry.
- New rendering styles.

Relevant docs:

- `docs/ARTIFACT_REPORTING_AUDIT.md`
- `docs/RENDERING_AUDIT.md`
- `docs/P1_INTEGRATION_FIXES.md`

Likely files/modules:

- `python/metrology_process_planner/workflows/artifacts/*`
- `python/metrology_process_planner/rendering/*`
- `python/metrology_process_planner/workflows/editor/render_bridge*`
- `python/metrology_process_planner/infrastructure/klayout/capture_adapter.py`

Tasks:

1. Audit remaining generator declarations and classify each as executable now or intentionally unavailable.
2. Register handlers for visual render artifacts that can be generated from existing solver/render contracts.
3. Use central artifact registry and owner refs only.
4. Add stable failure warnings and repair metadata.
5. Add deterministic test fixtures/goldens where useful.
6. Ensure report readiness improves after repair when the visual artifact is report-relevant.

Tests:

- generator unit tests
- repair service integration tests
- render/overview golden tests
- failure warning tests

Acceptance criteria:

- Selected missing/stale artifacts can become present.
- Generated files are registered centrally.
- Failures are structured and repairable.

Stop conditions:

- A visual generator requires a render contract that is not yet stable; document it as explicitly
  unavailable instead of adding a private renderer bypass.

Dependencies: solver/render tests already exist for render generators; live layout crop is already
covered by the injected KLayout exporter boundary.

## Packet 5: Finish Reporting Workbench Export Integration

Priority: P1

Goal: Make report export destination selection and artifact registration usable from the workbench.

Why: Reports are headless-capable, but the operator export path is incomplete.

Scope:

- destination picker
- export action callback
- readiness policy display
- output and manifest artifact registration
- result/status display

Out of scope:

- New report templates.
- Rewriting PPTX/PDF backends.

Relevant docs:

- `docs/ARTIFACT_REPORTING_AUDIT.md`
- `docs/P1_INTEGRATION_FIXES.md`
- `docs/TEST_PLAN_NEXT.md`

Likely files/modules:

- `python/metrology_process_planner/app/reporting_workbench*.py`
- `python/metrology_process_planner/ui/reporting_workbench/*`
- `python/metrology_process_planner/reporting/*`

Tasks:

1. Add fakeable destination picker.
2. Wire export action to `ReportGenerationService`.
3. Register manifest/output artifacts and refresh active document.
4. Render readiness and result rows.
5. Add tests for strict and placeholder policies.

Tests:

- `test_reporting_workbench_export_uses_selected_destination`
- `test_reporting_workbench_registers_manifest_artifact`
- `test_reporting_strict_missing_artifacts_blocks_export`
- `test_reporting_placeholder_policy_exports_with_warnings`

Acceptance criteria:

- Workbench exports to selected destination.
- Manifest and outputs are registered.
- Readiness behavior is explicit and tested.

Stop conditions:

- Artifact generator gaps block a template; use placeholder policy and document dependency on Packet 4.

Dependencies: Packet 1; Packet 4 improves output completeness.

## Packet 6: Align Product Mode Catalog

Priority: P1

Goal: Make visible modes match product scope and documentation.

Why: A roadmap cannot stabilize a mode system whose public catalog is ambiguous.

Scope:

- `fib_cut_planner` decision
- `process_flow_summary` visibility/policy decision
- `process_aware_metrology` visibility decision
- legacy `cdsem_capture` picker visibility

Out of scope:

- Building full FIB feature workflow if product decision is to descope.
- New solver physics.

Relevant docs:

- `docs/MODE_AUDIT.md`
- `docs/FEATURE_MATRIX.md`
- `docs/NEXT_PRIORITIES.md`

Likely files/modules:

- `python/metrology_process_planner/domains/session/mode_builtins.py`
- `python/metrology_process_planner/domains/session/mode_non_process_builtins.py`
- `python/metrology_process_planner/domains/session/mode_registry.py`
- mode picker UI from Packet 1

Tasks:

1. Decide visible product catalog.
2. Encode visibility/policy in mode definitions.
3. Add or remove/de-scope FIB from user-facing docs.
4. Hide legacy CDSEM alias from picker while preserving load.
5. Add diagnostics/picker tests.

Tests:

- visible mode catalog test
- legacy load compatibility test
- FIB/process-flow policy tests

Acceptance criteria:

- Mode picker and docs agree.
- All visible modes have coherent policy blocks.
- Legacy sessions still load.

Stop conditions:

- Product decision is required for FIB scope; document options and do not invent feature behavior.

Dependencies: Packet 1 for picker visibility.

## Packet 7: Add Installed External Mode Discovery

Priority: P1

Goal: Wire external JSON mode folders into app startup/configuration, diagnostics, picker selection, and durable session persistence.

Why: Loader exists, but installed users cannot benefit from it without host discovery.

Scope:

- configured external folders
- diagnostics loaded-mode warnings
- visible external mode picker selection
- registered custom mode ID persistence
- release/package policy

Out of scope:

- Executable custom mode code.
- Remote plugin downloads.

Relevant docs:

- `docs/MODE_AUDIT.md`
- `docs/P1_INTEGRATION_FIXES.md`

Likely files/modules:

- `python/metrology_process_planner/domains/session/mode_loader.py`
- `python/metrology_process_planner/domains/session/record.py`
- app bootstrap/config module
- KLayout session path adapter
- diagnostics summary
- `tools/package_manifest.py`

Tasks:

1. Add config source for external mode folders.
2. Load folders at app service bootstrap.
3. Preserve built-ins on external load failure.
4. Show loaded modes and warnings in diagnostics.
5. Allow visible registered custom mode IDs through new-session pickers.
6. Preserve registered custom mode IDs through save/reopen.
7. Add package/release policy tests.

Tests:

- app bootstrap configured folder test
- invalid mode warning test
- diagnostics loaded mode test
- custom mode document round-trip test
- KLayout picker external mode test
- package manifest/config policy test

Acceptance criteria:

- External modes can be discovered in installed context.
- Invalid external modes do not break startup.
- Diagnostics makes loaded mode state inspectable.
- Visible registered external mode IDs can create durable sessions.
- Unknown unregistered saved mode IDs still fall back with warnings.

Stop conditions:

- No agreed config location; document options and implement a local test-only config seam first.

Dependencies: Packet 6 recommended.
