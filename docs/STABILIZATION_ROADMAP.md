# Stabilization Roadmap

Last updated: 2026-06-25

## 1. Executive Summary

Overall product health: usable stabilized core, with remaining polish and release-evidence work. The Process Planner has a coherent document spine: `SessionRecord`, `SessionDocument`, mode policies, persisted captures, central artifacts, process context, solver/render contracts, reports, diagnostics, KLayout adapters, and broad automated tests. The P0/P1 command-path and integration blockers identified by the audit are resolved in pure/fakeable coverage; live installed-KLayout checks remain opt-in release lanes.

Input audit: all expected audit inputs were present and used for this roadmap: `FULL_FEATURE_AUDIT.md`, `FEATURE_MATRIX.md`, `MODE_AUDIT.md`, `UI_AUDIT.md`, `SESSION_DOCUMENT_AUDIT.md`, `ARTIFACT_REPORTING_AUDIT.md`, `RENDERING_AUDIT.md`, `TEST_COVERAGE_AUDIT.md`, `INTEGRATION_SEAMS.md`, `CONTRACT_MATRIX.md`, `DEPENDENCY_AUDIT.md`, `NO_BYPASS_AUDIT.md`, `E2E_WORKFLOW_AUDIT.md`, `KNOWN_LIMITATIONS.md`, and `NEXT_PRIORITIES.md`.

Analysis passes completed: P0 scan, duplicate/bypass scan, missing-test scan, user-flow scan, and contract-gap scan. No new feature work was started.

Top P0 blockers:

1. Resolved: top-level New/Open/Open Recent/Save As route through path/mode adapters and lifecycle services.
2. Resolved: Bind Current Layout records source layout context and restores durable overlay proxies through the KLayout adapter boundary.

Top P1 integration risks:

1. Resolved for stabilization: production editor shell renders the existing view-model contract.
2. Resolved for stabilization: high-value artifact repair paths have executable handlers or explicit unavailable routing.
3. Mostly resolved: reporting export destination/stale repair paths are integrated; shell polish and broader formats are P2.
4. Resolved for stabilization: visible mode catalog is aligned and thin/legacy modes are hidden or descoped.
5. Resolved for stabilization: configured external mode folders load into app bootstrap, diagnostics, picker, and editor policy.

Most important missing tests:

- Live installed-KLayout smoke for bind/export before release packaging.
- Screenshot/interaction coverage for setup guide, diagnostics, reporting, and final editor polish.
- Broader visual regression galleries for cross-section/report outputs beyond the overview label-stress golden.
- Broader GUI gesture automation.

Recommended next three work packets:

1. Reconcile historical audit/planning docs against current implementation evidence.
2. Run full release check with `--include-klayout` before packaging.
3. Broaden visual regression galleries for process/report outputs if visual polish enters scope.

## 2. Current Product State

| Subsystem | State | Practical read |
| --- | --- | --- |
| session/document lifecycle | healthy | Core new/open/save/save-as exists with fakeable and KLayout path adapters |
| mode system | healthy_with_scope_limits | Built-in and JSON mode definitions exist; visible catalog and installed external discovery are wired; custom modes remain data-only |
| non-process-aware modes | healthy | Process UI is guarded off and tests cover non-process behavior |
| process-aware modes | usable_with_scope_limits | Profilometry and ellipsometry core flows work; FIB is intentionally descoped and process-flow is hidden report-only |
| setup guide | healthy | State machine, commands, host-ready card models, and KLayout shell wiring are implemented |
| unified editor | usable_with_polish_gaps | Document-backed editor model and KLayout-backed shell exist; final visual polish remains |
| capture workflows | usable_with_gaps | Box capture works; child line/point flows work in core; standalone point and line now save as product workflows |
| measurements | usable_with_polish_gaps | Nested measurement records and artifacts exist; final prompt styling remains |
| artifact registry | healthy_with_scope_limits | Central registry, scanner, statuses, warnings, repair metadata, and high-value generators exist; lower-priority declarations are explicit unavailable |
| metadata export | usable_with_gaps | CSV metadata is strong; source layout binding and copy UI need finish |
| process context | healthy_with_gaps | Attach/validate/regenerate core exists; recipe path selection routes through host adapters; broader recipe editor polish remains |
| solver | healthy | Pure solver contracts and golden tests exist |
| renderer | usable_with_visual_qa_gaps | Render profiles, scene contracts, and visual process repair exist; broader galleries remain polish |
| overview labeling | healthy_with_visual_qa_gaps | Layout/leader contracts and dense label-stress golden coverage are in place; screenshot galleries remain polish |
| reporting | usable_with_polish_gaps | Headless backends, workbench export, artifact registration, and report repair work; final shell polish remains |
| diagnostics | healthy_with_polish_gaps | Service summaries/actions and structured dashboard shell exist; broader visual polish remains |
| tests | healthy_with_release_lane | Broad unit/golden/integration coverage and opt-in KLayout lanes exist; full release check should run before packaging |

## 3. P0 Blockers

### Resolved P0.1: Menu/start-screen session document lifecycle path and mode input

Status: resolved for the stabilization command path.

Implemented fix: `SessionLifecycleCommandService` routes New Session, Open Session, Open Recent, and Save As through fakeable `SessionPathAdapter` selections. KLayout registration injects `KLayoutSessionPathAdapter`, including mode selection and hidden-mode filtering.

Evidence:

- `tests/test_session_document_path_commands.py`
- `tests/test_klayout_session_path_adapter.py`
- `tests/test_session_document_lifecycle.py`

Residual scope: recent-session persistence across process restarts and visual dialog smoke are release/polish concerns, not document-lifecycle blockers.

Estimated residual risk: low.

### Resolved P0.2: Bind Current Layout to Session

Status: resolved for the stabilization command path.

Implemented fix: `SessionLayoutCommandService` routes bind-current-layout through a fakeable `SessionLayoutAdapter`. KLayout registration injects `KLayoutSessionLayoutAdapter`, updates `SourceLayoutContext`, emits mismatch warnings, and restores durable `CanvasObject` overlays through `CanvasOverlayManager`.

Evidence:

- `tests/test_session_layout_binding_commands.py`
- `tests/test_klayout_boundary.py`
- overlay restore tests

Residual scope: live installed-KLayout bind smoke should remain in the release checklist.

Estimated residual risk: low.

## 4. P1 Integration Fixes

### Resolved P1.1: Production editor shell contract

Status: resolved for stabilization. KLayout-backed shell factories consume the existing header, navigator, preview, inspector, action, and status view-model contracts.

Evidence: `tests/test_klayout_session_editor_shell.py`, session editor controller/command bridge tests, and live modeless command-surface UI probe.

Residual scope: final visual styling and screenshot polish remain post-stabilization work.

### Resolved P1.2: Artifact generator handlers

Status: resolved for the P1 stabilization contract. Registry, statuses, repair metadata, and generator declarations exist, and P1 generator declarations now have concrete or explicitly unavailable repair behavior.

Affected systems: artifact repair, reporting, process outputs, capture images, metadata export.

Root cause: Artifact lifecycle contracts were created before concrete generators were filled out.

Why it mattered: Users could see missing/stale artifacts, but repair was not trustworthy until core generators existed.

Implemented fix: CSV, placeholder SVG, measurement annotation, overview SVG, process-output JSON, PowerPoint report-output, KLayout-injected live layout crop, and visual process SVG repair route through central artifact repair services. Requirement routing distinguishes missing recipe/solver/live-layout/exporter prerequisites from missing handlers.

Files/modules likely involved:

- `python/metrology_process_planner/workflows/artifacts/generators.py`
- `python/metrology_process_planner/workflows/artifacts/generator_builtins.py`
- `python/metrology_process_planner/workflows/artifacts/repair.py`
- `python/metrology_process_planner/rendering/*`
- `python/metrology_process_planner/infrastructure/klayout/capture_adapter.py`
- `tests/test_artifact_repair_service.py`
- `tests/test_synthetic_artifact_pipeline.py`

Tests required:

- Unit tests per generator.
- Repair-service tests that convert missing/stale to present.
- Failure tests that create stable warning and repair metadata.
- Requirement-routing tests for live-layout generator declarations.
- KLayout smoke for live-layout generators.

Acceptance criteria:

- High-priority missing artifacts can be regenerated.
- Failed generation does not corrupt session state.
- Artifact owner refs and central registry stay synchronized.

Estimated risk: medium.

### P1.3: Reporting workbench export path is not fully integrated

Symptom: Report service/backends work, but operator destination selection and final shell export flow remain adapter work.

Affected systems: reporting workbench, artifacts, report manifest, UI handoffs.

Root cause: Headless service came before final KLayout/Qt export UX.

Recommended fix: Add destination selection, export action wiring, result display, and artifact registration refresh.

Tests required:

- Workbench export destination test.
- PPTX/PDF/CSV/images manifest registration test.
- Missing-artifact placeholder policy test.

Acceptance criteria:

- User can choose output destination.
- Report outputs and manifest are registered in artifacts.
- Readiness blocks strict exports and allows placeholder policy exports.

Estimated risk: medium.

### P1.4: Product mode catalog is inconsistent

Symptom: `fib_cut_planner` is requested by product scope but not registered. `process_flow_summary`
and `process_aware_metrology` are now hidden compatibility modes rather than operator-facing modes.

Affected systems: mode picker, setup guide, capture routing, process outputs, reports.

Root cause: Render/process capabilities exist independently from final product mode decisions.

Recommended fix: Keep FIB descoped until it has a complete declarative mode packet.
Keep `process_flow_summary` report-only/load-compatible and `process_aware_metrology` internal unless
a future product packet promotes either with full setup/capture/editor/report policy.

Tests required:

- Mode registry tests.
- Non-process/process mode separation tests.
- Mode picker visibility tests.

Acceptance criteria:

- User-facing mode catalog matches documentation.
- Legacy/internal modes are hidden or explicitly marked.
- Each visible mode has setup/capture/artifact/report policy.

Estimated risk: medium.

### P1.5: External mode discovery is test-only/core-only

Status: resolved for the stabilization contract.

Symptom: resolved. JSON mode loader, installed-host configuration seam, diagnostics visibility,
picker selection, and durable custom mode ID round-trip are covered for registered data-only modes.

Affected systems: mode registry, release packaging, diagnostics, mode picker, session document.

Root cause: resolved by app-level mode registry loading and open custom mode ID support on
`SessionRecord`.

Recommended fix: Keep custom modes data-only and validate policy completeness before treating a
loaded mode as product-ready.

Tests required:

- App-level configured folder load test.
- Invalid folder/file warnings test.
- Package/release manifest test.
- KLayout picker external mode ID test.
- Registered custom mode save/reopen test.

Acceptance criteria:

- Host install can discover configured external mode folders.
- Invalid modes fail gracefully and visibly.
- Built-ins remain available if external loading fails.
- Visible registered external mode IDs can be selected for new sessions.
- Registered custom mode IDs round-trip through saved session JSON.
- Unregistered unknown IDs still fall back with `unsupported_mode` warnings.

Estimated risk: medium.

## 5. Test Gaps

| Subsystem | Missing tests |
| --- | --- |
| session document | file-picker New/Open/Open Recent/Save As, cancel behavior, recent-session persistence |
| modes | FIB remains descoped; custom mode policy completeness for product-ready external modes |
| UI/view models | dirty prompt rendering and disabled reasons in broader real widgets |
| capture | live overlay restore after reopen/bind, broader GUI gesture coverage |
| measurements | post-save prompt rendering in Qt shell |
| artifacts | relink picker, generator failure warning stability, lower-priority declaration-only generator policies |
| solver | no immediate P0/P1 gap; keep strict-mode and golden contract tests |
| renderer | broader visual galleries for cross-section/report outputs |
| overview labeling | no immediate stabilization gap; keep dense label-stress golden in regression |
| reporting | destination picker, export result display, manifest registration in UI flow |
| diagnostics | production dashboard rendering and action callbacks |
| end-to-end workflows | full operator path from menu to session creation, capture, measurement, repair, and report |

## 6. Recommended Fix Order

1. Wire explicit session document lifecycle UI adapters: New Session, Open Session, Open Recent, Save As.
2. Implement Bind Current Layout to Session and overlay restore against live KLayout.
3. Stabilize the production session editor shell around `SessionDocument` only.
4. Keep artifact generator handlers in regression coverage and clean up remaining lower-risk declaration-only policies.
5. Stabilize report export destination and workbench output registration.
6. Resolve mode catalog inconsistencies: FIB, process flow, process-aware metrology, legacy CDSEM visibility.
7. Keep live layout-crop and stale report-output repair in regression coverage.
8. Polish setup guide and diagnostics production shells.
9. Keep dense overview regression in coverage and add broader cross-section/report visual galleries later.
10. Keep broader live KLayout GUI gesture coverage in the opt-in release lane.

## 7. Work Packets for Agents

The agent-sized packets are defined in `docs/AGENT_WORK_PACKETS.md`. P0/P1 stabilization packets have landed for the pure/fakeable contract. Remaining work is polish, visual QA, release-lane evidence, and any future scoped product modes.

Recommended next command for Codex:
Run a completion audit against docs/STABILIZATION_ROADMAP.md and docs/NEXT_PRIORITIES.md before adding new feature work.
