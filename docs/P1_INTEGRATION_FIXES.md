# P1 Integration Fixes

Last updated: 2026-06-25

P1 means a major feature exists but is not reliably stitched into the rest of the product. These should follow the P0 blockers and precede feature expansion. The 2026-06-25 completion pass ran `python -m tools.release_check --include-klayout` successfully, so remaining P1 notes are release polish or future breadth rather than current stabilization blockers.

## Resolved P1.1: Production Session Editor Shell

Status: resolved at the integration-contract level. The KLayout plugin injects a KLayout-backed
`SessionEditorWidgetFactory` into the existing `SessionEditorShell`, and that factory now creates
Qt-backed header, action, navigator, preview, inspector, and status regions from existing view
models while preserving fakeable region state for tests.

Residual symptom: final visual polish and screenshot coverage remain useful release work, but the
operator shell no longer depends on the in-memory backend contract only.

Affected systems: session editor, pending review, metadata editing, artifact repair, process context, reporting handoff, dirty-state UI.

Implemented fix: Rendered existing header, navigator, preview, inspector, action, and status
contracts in the KLayout widget factory. No mode-specific review dialogs were introduced.

Files/modules:

- `python/metrology_process_planner/ui/session_editor/*`
- `python/metrology_process_planner/app/session_editor_surface.py`
- `python/metrology_process_planner/workflows/editor/*`

Tests required:

- production shell structural test for all regions: implemented for the KLayout-backed factory
- action callback tests through existing controller and command-router tests
- dirty/pending blocker UI tests
- screenshot/visual smoke once the Qt shell exists

Acceptance criteria:

- Widgets consume view models, not raw JSON.
- Pending simple/composite/measurement review is inside the unified editor.
- Disabled reasons are visible.
- Dirty close and save/discard paths are rendered and tested.

Residual risk: medium-low; visual screenshot coverage should still be added before release.

## P1.2: Concrete Artifact Generators

Status: resolved for the stabilization P1 scope. CSV export repair, placeholder SVG generation, measurement
annotation regeneration, overview SVG repair, process-output JSON regeneration/export, and
PowerPoint report-output regeneration now have registered built-in handlers and repair-service
tests. Live layout crop repair is implemented when the KLayout plugin injects a live crop exporter.
Profile, cross-section, full-stack, point-stack, and process-flow visual process artifacts repair
through role-specific solver/render SVG generation. Handler gaps now surface as explicit unavailable
repair requests.

Symptom: Artifact registry and repair services exist, and P1 generator declarations now have concrete or explicitly unavailable repair behavior.

Affected systems: artifact repair, reporting readiness, layout crops, measurement annotations, overview images, process render outputs.

Recommended remaining fix: broaden report/output-format repair only where additional formats become operator-critical.

Files/modules:

- `python/metrology_process_planner/workflows/artifacts/*`
- `python/metrology_process_planner/workflows/artifacts/generator_handlers.py`
- `python/metrology_process_planner/rendering/*`
- `python/metrology_process_planner/workflows/editor/render_bridge*`
- `python/metrology_process_planner/infrastructure/klayout/capture_adapter.py`

Tests required:

- generator unit tests: partially implemented in `tests/test_artifact_generator_handlers.py`
- repair-service integration tests: partially implemented
- failure path warnings
- artifact owner/ref synchronization tests

Acceptance criteria:

- Missing/stale high-priority artifacts can be regenerated.
- Generated artifacts register central records and owner refs.
- Failures produce stable warnings and repair metadata.

Implemented evidence:

- stale CSV export rebuilds through `csv_export`
- placeholder artifacts write visible SVG files through `placeholder_image`
- measurement-owned annotation artifacts refresh through the existing render bridge and preserve
  measurement owner refs
- overview SVG artifacts regenerate through `overview_diagram_renderer`
- process-output JSON artifacts regenerate through the existing process solver and
  `ProcessOutputStore`
- PowerPoint report-output artifacts regenerate through the headless reporting service from saved
  `ReportRecord` metadata and update central report artifact refs
- layout-crop artifacts regenerate through `layout_crop_repair_service` when a live
  `KLayoutLayoutCropExporter` is injected by the KLayout plugin
- profile, cross-section, full-stack compressed, point-stack, and process-flow visual artifacts
  regenerate as SVGs through role-specific solver/render generator handlers
- generic process-output JSON artifacts continue to repair through `ProcessOutputStore`
- missing recipe/solver context is represented as unavailable repair requirements for process
  output artifacts
- generator declarations without concrete handlers return `GENERATOR_HANDLER_UNAVAILABLE` instead
  of available-but-dead repair actions
- live-layout generator declarations now set `requires_live_layout`; layout crop repair requests
  report `SOURCE_LAYOUT_REQUIRED_FOR_REPAIR` until a source layout is bound
- the KLayout plugin now injects `layout_crop_repair_service(KLayoutLayoutCropExporter(...))`,
  allowing selected missing/stale layout-crop artifacts to repair through the central editor
  artifact command path when a live KLayout view exporter is available
- generator handlers that update session records return `ArtifactGenerationResult`

Risk: low; remaining work is format breadth and visual QA rather than a P1 integration blocker.

## P1.3: Reporting Workbench Export Integration

Status: mostly resolved. Destination selection now routes through a fakeable
`ReportOutputAdapter`, the workbench stores the selected folder on `ReportRequest`, exports into
that folder, KLayout registration supplies a Qt folder picker, and stale readiness routes to a
distinct `regenerate_stale` action. PowerPoint report outputs now have concrete built-in repair
through the headless reporting service. Remaining work is production shell polish and broader
non-PPTX report-output repair coverage if those formats become operator-critical.

Symptom: Report service/backends are usable headlessly, and destination selection is now wired.
Stale PowerPoint report-output repair now has explicit workbench routing and a concrete repair
handler behind the built-in artifact repair service.

Affected systems: reporting workbench, report readiness, artifacts, export manifest.

Recommended remaining fix: Keep production shell polish in release work and broaden report-output
repair to PDF/CSV/image bundles only if those formats become first-class operator outputs.

Files/modules:

- `python/metrology_process_planner/app/reporting_workbench*.py`
- `python/metrology_process_planner/app/report_output_adapter.py`
- `python/metrology_process_planner/ui/reporting_workbench/*`
- `python/metrology_process_planner/reporting/*`

Tests required:

- export destination test: implemented
- stale action routing test: implemented
- stale/missing PowerPoint report artifact repair tests: implemented
- strict vs placeholder readiness tests
- manifest and artifact registration test
- UI action callback test
- KLayout output-folder adapter test: implemented

Acceptance criteria:

- User chooses export destination: implemented through `choose_output`.
- PPTX/PDF/CSV/images outputs can be produced from saved document state.
- Report manifest is registered.
- Missing artifacts are blocked or placeholdered according to policy.
- Stale/missing generated PowerPoint report artifacts can be rebuilt from saved session state.

Risk: medium.

## P1.4: Mode Catalog Alignment

Status: resolved for stabilization. The visible operator catalog now excludes legacy/internal/thin
compatibility modes while keeping them registered for saved-session load compatibility.
`fib_cut_planner` is explicitly descoped from this stabilization pass rather than added as a thin
mode.

Symptom: `fib_cut_planner` is promised but not registered; `process_flow_summary` is thin; `process_aware_metrology` is ambiguous; `cdsem_capture` is a legacy duplicate.

Affected systems: mode picker, setup guide, capture routing, reports, diagnostics.

Implemented fix: Make the visible mode catalog match implemented product scope. `cdsem_capture`,
`process_aware_metrology`, and `process_flow_summary` are hidden from picker-facing catalogs.
KLayout new-session mode selection uses `ModeRegistry.visible_mode_ids()`. `fib_cut_planner` stays
out of the visible catalog until a complete mode implementation is scheduled.

Files/modules:

- `python/metrology_process_planner/domains/session/mode_builtins.py`
- `python/metrology_process_planner/domains/session/mode_non_process_builtins.py`
- `python/metrology_process_planner/domains/session/mode_registry.py`
- mode picker/start-screen UI files added by P0.1

Tests required:

- mode registry visibility test: implemented
- mode picker visible catalog test: implemented for KLayout adapter
- legacy load compatibility test
- process/non-process guard tests

Acceptance criteria:

- Visible mode list is intentional.
- Each visible mode has capture, setup, artifact, editor, and reporting policies.
- Legacy modes can load but need not appear in picker.

Risk: medium.

## P1.5: Installed External Mode Discovery

Status: resolved for the stabilization contract. App bootstrap now loads external JSON mode folders
from `MPP_MODE_DEFINITION_DIRS`; diagnostics shows loaded external modes and load warnings. Picker
selection accepts visible external registry IDs, registered custom mode IDs persist through
`SessionDocument` as durable open `SessionModeId` strings, and the generic editor builder/adapter
uses the injected registry when deriving setup groups, dashboard actions, measurement affordances,
and mode metadata fields.

Symptom: resolved. External JSON mode loader, app-level discovery/configuration, diagnostics
visibility, picker selection, document round-trip, and editor policy projection are wired for
registered data-only modes.

Affected systems: mode registry, release packaging, diagnostics, mode picker.

Recommended remaining fix: Keep custom mode behavior policy-driven. Do not add executable custom
mode code; validate that each loaded `ModeDefinition` declares enough setup/capture/editor/report
policy for the generic workflow it is expected to use.

Files/modules:

- `python/metrology_process_planner/domains/session/mode_loader.py`
- `python/metrology_process_planner/domains/session/record.py`
- `python/metrology_process_planner/app/mode_registry_config.py`
- app bootstrap/configuration module
- `python/metrology_process_planner/infrastructure/klayout/session_path_adapter.py`
- `tools/package_manifest.py`
- diagnostics summary

Tests required:

- app-level external folder load test: implemented
- invalid/missing folder warning test: implemented
- package manifest test
- diagnostics loaded-mode test: implemented
- registered custom mode document round-trip test: implemented
- registered custom mode editor-policy projection test: implemented
- KLayout picker external mode ID test: implemented

Acceptance criteria:

- Built-ins load even when external folders fail.
- Configured external modes appear in registry and diagnostics.
- Invalid external modes are warnings, not crashes.
- External modes appear in picker when they are visible in the loaded registry.
- Registered custom mode IDs persist through save/reopen without `unsupported_mode` warnings.
- Registered external mode policies shape generic editor view models without custom executable code.
- Unregistered saved custom IDs still fall back with `unsupported_mode` warnings.

Risk: medium.
