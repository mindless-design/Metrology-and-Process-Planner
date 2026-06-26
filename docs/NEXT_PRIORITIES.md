# Next Priorities

Last updated: 2026-06-25

Priorities are ranked by foundational risk, user impact, integration risk, test coverage, and dependency on other features.

## P0 - Foundational Blockers

| Priority | Work | Why | Dependencies | Acceptance evidence |
| --- | --- | --- | --- | --- |
| P0.1 | Wire menu/start-screen New Session, Open Session, Open Recent, and Save As to Qt/KLayout file and folder pickers | resolved | `SessionEditorLifecycleMixin`, `SessionStore`, `RecentSessionRegistry` | Lifecycle command adapter tests pass; KLayout plugin supplies `KLayoutSessionPathAdapter` |
| P0.2 | Implement Bind Current Layout to Session | resolved | `SourceLayoutContext`, `CanvasOverlayManager`, KLayout view adapter | Bind command tests pass; KLayout plugin supplies current-layout adapter and overlay backend |

## P1 - Must Fix Before Feature Expansion

| Priority | Work | Why | Dependencies | Acceptance evidence |
| --- | --- | --- | --- | --- |
| resolved | Add production Qt shell for unified editor view models | KLayout shell now renders Qt-backed regions from the existing `SessionEditorShell` contract | existing editor shell contracts | `test_klayout_session_editor_shell_renders_document_regions`, session editor shell controller tests, `pytest` |
| resolved | Continue concrete artifact generators for visual cross-section/profile outputs | CSV, placeholder, measurement annotation, overview SVG, process-output JSON, PowerPoint report-output repair, live-layout requirement routing, injected live layout-crop repair, and visual process SVG repair are implemented | artifact generator registry, renderers, KLayout adapter | visual process artifact generator tests, artifact handler tests, and layout crop tests pass |
| resolved_for_stabilization | Finalize report export destination UX | Workbench now chooses destination through an adapter, exports there, routes missing/stale repair actions distinctly, and repairs generated PowerPoint report outputs through the built-in repair service | reporting workbench/service | `choose_output`, export-to-selected-folder, stale-action, report repair, and KLayout adapter tests |
| resolved | Align visible mode catalog and descope `fib_cut_planner` for stabilization | Visible catalog now excludes legacy/internal/thin modes; FIB remains out until a complete mode packet | mode registry, KLayout picker | visible catalog tests and hidden-mode picker tests pass |
| resolved | Add installed external mode discovery/configuration | App loads configured external folders, diagnostics shows warnings, and visible external mode IDs can be selected, persisted, and projected into generic editor policy | mode loader, app config, diagnostics, session document, editor builder/adapter | app-level configured-folder, diagnostics, picker, custom mode round-trip, and editor-policy tests pass |

## P2 - Important Capability and Polish

| Priority | Work | Why | Dependencies | Acceptance evidence |
| --- | --- | --- | --- | --- |
| resolved | Polish setup guide Qt cards and status badges | Setup-guide card models and KLayout setup shell now render status, requirement, artifact, warning, action, disabled, and active-stage metadata | setup guide view models | setup-guide card model tests and KLayout setup-guide shell tests pass |
| resolved | Polish diagnostics dashboard | Diagnostics now has grouped dashboard sections for session, workflow, artifacts, process/report state, activity, and actions | diagnostics controller/shell | diagnostics dashboard tests pass |
| resolved | Clarify and strengthen `process_flow_summary` mode | It is explicitly hidden, report-only, load-compatible, and mapped to process-flow reporting | mode registry, process-flow renderer/report template | mode audit and mode registry tests show report-only compatibility policy |
| resolved | Add dense real-layout overview visual regression | Dense label-stress geometry now has golden overview summary coverage | overview renderer | `test_dense_real_layout_overview_matches_golden_summary` |
| resolved | Hide/deprecate legacy `cdsem_capture` in operator picker | `cdsem_capture` is hidden while `cdsem_measurement` remains visible and legacy sessions remain load-compatible | mode picker | visible catalog and alias tests pass |
| resolved | Finish recipe picker/open-file shell | Recipe open, save-as, and setup attach now use production path adapters through command/service boundaries | recipe editor/session attachment | recipe path adapter command tests and KLayout adapter tests pass |

## P3 - Later Enhancements

| Priority | Work | Why | Dependencies | Acceptance evidence |
| --- | --- | --- | --- | --- |
| resolved | Standalone point capture product workflow | Generic Shift-click point capture now creates a pending point capture and saves as a first-class capture | point capture tool, pending review | standalone point capture tests and KLayout boundary tests pass |
| resolved | Standalone line capture product workflow | Parentless Shift-drag line capture now creates a pending line capture and saves as a first-class capture while parented line gestures still create measurements/profile features | line capture tool, pending review | standalone line capture tests and KLayout boundary tests pass |
| resolved | Broader live KLayout GUI gesture automation | KLayout release lanes now cover menu registration, main-window snapshot, modeless command surfaces, GUI capture surfaces, and batch capture adapter contracts for standalone/product gestures | KLayout UI runner, batch `pya` probes | 10 opt-in batch probes and 4 opt-in live GUI probes cover the KLayout boundary |
| resolved_for_stabilization | More sophisticated process solver physics | Expanded synthetic fixtures now declare executable accuracy envelopes and etch operations emit target-exhaustion/non-target-blocker diagnostics; calibrated physics remains future product scope | solver kernels/goldens | solver fixture metadata tests, etch diagnostic tests, and `docs/SOLVER_ACCURACY_ENVELOPE.md` |

## Immediate Slice

The stabilization roadmap is complete for the current contract. P1.2 core repair handlers, visual process repair, report repair, live-layout requirement routing, and injected live layout-crop repair; P1.3 output destination/stale-action routing; P1.4 visible catalog alignment; P1.5 external discovery/custom mode selection/editor policy; P2.1 setup-guide card polish; P2.2 diagnostics dashboard polish; P2.3 process-flow report-only policy; P2.4 dense overview regression; P2.5 CDSEM legacy hiding; P2.6 recipe picker/open-file shell; P3.1 standalone point capture; P3.2 standalone line capture; P3.3 live KLayout GUI automation; and the P3.4 solver accuracy/etch diagnostic envelope are implemented. Next work should be chosen intentionally as release polish, broader visual galleries, or a new product feature packet.
