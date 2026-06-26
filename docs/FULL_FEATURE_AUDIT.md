# Full Feature Audit

Last updated: 2026-06-25

## Executive Summary

The Process Planner plugin is a document-centered KLayout plugin with a substantial pure-Python core. The strongest implemented areas are canonical session JSON, mode policy records, editor view models, artifact registry and repair metadata, solver/render contracts, reporting backends, diagnostics summaries, and automated unit/golden/integration coverage.

The main product risk is not that core records are missing. The previously identified P0/P1 seams now have fakeable service adapters, KLayout boundary adapters, and regression coverage. Remaining risk is mostly product polish and release evidence: broader live visual QA, final reporting-shell polish, intentionally descoped FIB mode scope, and keeping opt-in KLayout lanes current.

No P0 data-model or command-path blocker remains in the automated stabilization evidence. Session JSON, captures, artifacts, modes, solver output, reports, lifecycle commands, and bind-current-layout seams are covered by unit/integration tests. Live KLayout evidence remains opt-in release-lane validation rather than a core-data blocker.

## P0 Blockers

| Blocker | Status | Evidence | Impact | Next Action |
| --- | --- | --- | --- | --- |
| Menu-level explicit New/Open/Open Recent/Save As path input | resolved | `SessionLifecycleCommandService`, `SessionPathAdapter`, `KLayoutSessionPathAdapter`, `test_session_document_path_commands`, `test_klayout_session_path_adapter` | Normal supplied-input command paths create/open/recent/save-as documents through `SessionDocument` | Keep picker cancellation and live KLayout dialog behavior in release-lane checks |
| Bind current layout to session | resolved | `SessionLayoutCommandService`, `KLayoutSessionLayoutAdapter`, `test_session_layout_binding_commands`, `test_klayout_boundary` | Source layout context persists and overlays restore through durable `CanvasObject` records | Keep a live installed-KLayout bind smoke before release packaging |

## Major Feature Inventory

| Feature | Status | User-facing entrypoint | Primary modules/classes | Data models used | Session JSON support | Artifact support | UI support | Tests | Known issues | Recommended next action |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| KLayout menu and command router | implemented | Tools > Metrology Process Planner | `infrastructure.klayout.plugin`, `app.command_catalog`, `ui.shell.command_router` | `CommandSpec`, `CommandId`, `CommandRouteResult` | n/a | n/a | Stable menu metadata plus modeless command surfaces | command registry, UI redesign, KLayout UI automation | release-lane breadth must stay current | Keep opt-in GUI probes in release check |
| New/Open/Recent session | implemented | New Session, Open Session, Open Recent, editor start screen | `SessionEditorLifecycleMixin`, `SessionStore`, `RecentSessionRegistry`, `SessionLifecycleCommandService` | `SessionRecord`, `SessionDocument`, `NewSessionRequest` | implemented load/save/migrate/preserve | creates managed folders | path/mode adapter boundary is fakeable and KLayout-backed | lifecycle, path-command, KLayout path-adapter tests | recent-session persistence beyond process lifetime is future polish | Keep dialog smoke in release lane |
| Save/Save As/Close/dirty state | implemented_with_polish_gaps | editor header, Save Session, Save As, Close Session, End Active Session | `SessionEditorLifecycleMixin`, `SessionLifecycleService`, `SessionDocumentWriter` | `DirtyState`, `ActiveSessionContext` | atomic write, backup, unknown top-level preservation | n/a | save/close and Save As adapter paths wired | lifecycle and command bridge tests | final dirty prompt visual polish | Keep command behavior covered |
| Mode registry | implemented | session creation/editor mode display | `ModeDefinition`, `ModeRegistry`, built-ins, JSON loader | `SessionMode`, policy blocks | mode id persists in `session.mode` | mode artifact policies | editor/setup/reporting consume policies | mode registry, mode validation, config, non-process tests | product-ready custom modes remain policy-only | Keep external modes data-only |
| Non-process modes | implemented | mode selection/session mode | `mode_non_process_builtins`, `mode_grid_builtin` | mode policies | persisted | capture/grid/report artifacts | recipe/process hidden by policy | non-process hardening tests | `cdsem_capture` legacy alias coexists with `cdsem_measurement` | Keep process guards enforced |
| Process-aware modes | implemented_with_scope_limits | Profilometry, Ellipsometry; Process Flow Summary is report-only compatibility | `mode_builtins`, compound workflow, process context | process policies, `ProcessContext`, `ProcessOutputRecord` | persisted | placeholders and process-output records | editor dashboard/process actions | compound/process/mode tests | `fib_cut_planner` is intentionally descoped until complete | Do not expose FIB until a full mode packet exists |
| Setup guide | implemented | Start / Resume Measurement Setup | `SetupGuideController`, `SetupGuidePresenter`, `SetupGuideStateMachine` | `SetupState`, setup stage snapshots | setup state persists | setup artifact badges inspect registry | KLayout-backed setup card shell | setup guide state/command/card/shell tests | live visual polish still useful | Continue visual QA in release lane |
| Box capture | implemented | Start Capture, Start Box Capture, Shift-drag | `BoxCaptureTool`, `CanvasInteractionEngine` | `PendingCapture`, `CanvasObject`, `CaptureRecord` | pending/saved state persists via extensions/captures | pending image paths and site image refs | shared status presenter | capture/canvas tests, KLayout smokes | live overlay rebinding needs layout binding | Wire final KLayout view adapter polish |
| Line capture | implemented | Start Line Capture, Add Measurement, compound line child | `LineCaptureTool`, `measurement_workflow`, standalone line commit, compound routing | `CaptureRecord`, `MeasurementRecord`, line feature payloads | standalone lines, measurement lines, and feature lines persist | annotation/detail placeholders for measurements; line captures use normal capture artifacts | editor actions wired | standalone line, measurement, compound, KLayout boundary, live GUI capture-surface tests | visual polish only | Keep parentless and parented routing covered |
| Point capture | implemented | Start Point Capture, ellipsometry child point | `PointCaptureTool`, pending point commit, compound point routing | point geometry and point feature payloads | standalone and ellipsometry child point persist | point/stack placeholders | pending review and compound point UI | standalone point, point boundary, compound tests | live visual polish remains | Continue release-lane UI verification |
| Compound captures | implemented_with_polish_gaps | Profilometry/Ellipsometry mode capture | compound capture modules | composite capture geometry/features | parent and child records persist | placeholders for process roles | unified editor pending composite review | compound workflow/reload tests | production UI polish remains | Add richer process-output artifacts only if scoped |
| Persistent overlays | implemented | capture/measurement selection | `CanvasObject`, `CanvasOverlayManager`, selection coordinator | canvas objects in `extensions.canvas` | durable overlay proxies persist; UI is not canonical | n/a | restore commands and indexes exist | overlay/selection/reload/bind tests | live release smoke remains useful | Keep overlays non-canonical |
| Unified session editor | implemented_with_polish_gaps | Session Editor | `SessionEditorController`, `SessionDocumentBuilder`, adapters, shell | `SessionDocument`, item/view models | reads/writes canonical document | previews inspect artifact registry | KLayout-backed shell renders regions | editor and KLayout shell tests | final visual polish | Keep widgets on view-model contracts |
| Measurement workflow | implemented_with_polish_gaps | Add Measurement from saved capture | `measurement_workflow`, `measurement_completion`, editor commands | nested `MeasurementRecord` | nested under capture | pending/regenerable annotation artifacts | editor pending measurement actions | measurement tests | final prompt visual styling | Keep measurement nesting and artifact tests green |
| Artifact registry and repair | implemented_with_scope_limits | editor artifact actions, diagnostics | `ArtifactRecord`, `ArtifactScanner`, `ArtifactRepairService` | central `artifacts` map, local refs | first-class persisted registry | statuses, dependencies, repair metadata | repair actions and diagnostics | artifact/generator/report repair tests | lower-priority declarations may remain intentionally unavailable | Keep no-handler paths explicit |
| Metadata export | implemented | Export CSV | `CaptureCsvExporter`, CSV row/schema modules | captures/features/measurements/source layout | data from JSON | CSV artifact registration exists through editor export commands | editor export action | CSV/export tests | copy actions are view-model level, not polished UI | Wire UI affordances for copy coordinates |
| Recipe/process context | implemented | Edit Recipe, Attach Recipe, Validate Process Context | recipe editor, process context workflow, recipe path adapters | `ProcessContext`, warnings, process output records | persisted and migrated | process-output placeholders | editor/dashboard/setup actions | process context and recipe path adapter tests | live visual polish remains | Continue release-lane UI verification |
| Process solver | implemented_with_envelope | process-output regeneration | `HybridCrossSectionSolver`, operations, solver models | `SolverInput`, `SolverResult`, diagnostics | solver summaries in process outputs/artifacts | JSON summaries; render integration exists | indirect via editor process actions | solver contract/golden/envelope tests | approximate geometry model by design | Keep strict-mode/golden and accuracy-envelope discipline |
| Renderer pipeline | implemented_with_visual_qa_gaps | render bridge, process output regeneration, report generation | cross-section/overview/rendering modules | `RenderIntent`, `RenderProjection`, scene models | derived artifacts referenced | SVG/PDF/PPTX/images supported in parts | editor/reporting previews | render and visual process repair tests | broader visual galleries still useful | Add visual reviews as post-stabilization polish |
| Overview labeling | implemented_with_visual_qa_gaps | overview/report artifact generation | `rendering.overview` | overview request/scene/labels/leaders | derived artifact records | SVG overview artifact | report/editor integration | overview and dense golden tests | broader screenshot gallery remains polish | Keep dense golden summary in regression |
| Reporting/export | implemented_with_polish_gaps | Reporting Workbench, Build Report | `ReportGenerationService`, backends, workbench | `ReportRequest`, `ReportDocument`, manifest | reads saved session document | PPTX/PDF/CSV/images/manifest | modeless workbench exists with output adapter | reporting/workbench/repair tests | final shell polish and broader format repair | Keep report outputs registry-backed |
| Diagnostics | implemented | Advanced Diagnostics | `AdvancedDiagnosticsController`, summaries, snapshots, dashboard models | diagnostics events/snapshots | inspects session/editor/window state | debug bundle/action handoffs | grouped dashboard/action shell | diagnostics tests | live visual polish remains | Continue visual QA in release lane |
| Tests and release gates | implemented | pytest, unittest, release check | tests, tools | fixtures and golden data | broad fixture coverage | artifact/render/report tests | KLayout opt-in lanes | many tests | live GUI breadth still limited | Add UI-adapter tests for remaining unavailable commands |

## Process-Aware vs Non-Process Separation

Non-process modes use `non_process_mode(...)`, set process policy to forbidden/none, and have tests that assert recipe/process UI is hidden. Process-aware modes declare recipe policy, solver operation, process context visibility, process-output placeholders, and process dashboard actions. Current separation is implemented, with the main remaining risk in future mode additions and external mode loading.

## User-Visible Missing or Duplicated Areas

- `fib_cut_planner` is requested by the audit brief but is not present as a built-in `SessionMode` or mode definition. The renderer has FIB full-stack profile support and canvas object types include `fib_cut`, but the product mode is not started as a full user-facing mode.
- `process_flow_summary` exists as a hidden report-only/load-compatible mode id and report template; capture/setup/editor workflow is intentionally absent until a complete workflow is scoped.
- `process_aware_metrology` exists in code but is not in the brief's built-in mode catalog; document it as legacy/internal or decide whether to expose it.
- `cdsem_capture` remains as a legacy alias next to `cdsem_measurement`. This is intentional compatibility, but it should not clutter operator mode selection.
- General standalone point capture now creates and saves first-class point captures outside compound point workflows.

## Highest Risks

1. UI polish: editor/setup/reporting/diagnostics shells are fakeable and testable but not final visual design.
2. Visual QA breadth: process/report image galleries remain thinner than the document/workflow tests.
3. Release evidence: live installed-KLayout bind/export smokes should be kept in the release checklist.
4. Product scope: FIB remains intentionally descoped until a complete declarative mode packet exists.
5. External modes: custom modes remain data-only and constrained to shared declarative policies.

## Recommended Next Fixes

1. Keep release-lane KLayout bind/export smokes current before packaging.
2. Add visual galleries for cross-section/profile/report outputs if visual polish enters scope.
3. Add `fib_cut_planner` only as a complete declarative mode packet, not as a partial mode.
4. Keep lower-priority artifact generators either executable or explicitly unavailable.
5. Re-run full pytest, quality gates, and release checks before declaring a shippable stabilization tag.
