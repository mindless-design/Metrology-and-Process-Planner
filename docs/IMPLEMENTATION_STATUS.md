# Process Planner Implementation Status

Last updated: 2026-06-25

## Current Roadmap Pass

- Current packet: Completion audit passed for the current stabilization roadmap scope.
- Completed packets: Packet 1, Wire Session Document Lifecycle UI Adapters; Packet 2, Bind Current Layout And Restore Overlays; Packet 3, Stabilize Production Session Editor Shell; Packet 4, Artifact Repair And Generator Handoffs; Packet 5, Reporting Workbench Export Integration; Packet 6, Mode Catalog Alignment; Packet 7, Installed External Mode Discovery; Packet 8, Report Artifact Repair Handoff; Packet 9, Live Layout Crop Repair; Packet 10, Visual Cross-Section/Profile Repair Breadth; Packet 11, Setup Guide Qt Polish; Packet 12, Diagnostics Dashboard Polish; Packet 13, Process Flow Summary Mode Clarification; Packet 14, Dense Real-Layout Overview Visual Regression; Packet 15, Legacy CDSEM Alias Deprecation; Packet 16, Recipe Picker/Open-File Shell; Packet 17, Standalone Point Capture Product Workflow; Packet 18, Standalone Line Capture Product Workflow; Packet 19, Broader Live KLayout GUI Gesture Automation; Packet 20, Process Solver Physics Expansion.
- Packet 7 result: app-level external mode folder discovery, diagnostics visibility, canonical open custom mode IDs, and registry-driven editor policy for loaded external modes are implemented.
- Packet 8 result: generated report outputs now register repair metadata and dependency signatures, saved PowerPoint deck/report-manifest artifacts route to `REBUILD_REPORT`, and the built-in repair service can regenerate missing or stale report deck artifacts from `SessionDocument` without live UI state.
- Packet 9 result: live layout crop repair is wired through `layout_crop_repair_service`, injected into KLayout plugin registration via `KLayoutLayoutCropExporter`, and remains unavailable in the default headless repair path until a live exporter is supplied.
- Packet 10 result: profile, cross-section, full-stack, point-stack, and process-flow visual process artifacts now repair through role-specific solver/render SVG generation, while generic process-output JSON repair remains available as a fallback.
- Packet 11 result: setup-guide stage cards now have display-ready status, requirement, artifact, warning, and action badge models, and KLayout registration injects a Qt-backed setup-guide surface factory.
- Packet 12 result: diagnostics shell now renders a structured dashboard model with grouped session, workflow, artifact, process/report, activity, and action state, including session path, dirty state, solver/render backend, and report readiness rows.
- Packet 13 result: `process_flow_summary` is documented and tested as a hidden report-only/load-compatible mode, with process solver forbidden and process-flow reporting template selection preserved.
- Packet 14 result: dense real-layout overview label routing is covered by the label-stress GDS-derived golden fixture and split into a dedicated quality-compliant regression test.
- Packet 15 result: legacy `cdsem_capture` remains load-compatible but hidden from operator mode pickers, while `cdsem_measurement` is the visible CDSEM mode.
- Packet 16 result: recipe open, save-as, and setup attach commands now use host recipe path adapters; KLayout registration injects the recipe JSON picker adapter without letting UI write recipe/session state directly.
- Packet 17 result: generic Shift-click point capture now creates a standalone pending point capture with canonical point geometry, KLayout point gestures update session/overlay state, and pending review can save the point as a first-class capture record.
- Packet 18 result: parentless Shift-drag line capture now creates a standalone pending line capture with canonical line geometry, KLayout line gestures update session/overlay state, and pending review can save the line as a first-class capture record without changing parented measurement/profile line behavior.
- Packet 19 result: opt-in KLayout automation now covers menu registration, main-window snapshot, modeless command surfaces, GUI capture-surface contracts, and batch `pya` capture-adapter probes for measurement line, profilometry line, ellipsometry point, standalone line, and standalone point routing without source-layout mutation.
- Packet 20 result: executable synthetic solver fixtures now declare accuracy envelopes that distinguish contract, qualitative, visual, and workflow claims from excluded calibrated physics; etch operations now emit explicit target-exhaustion and non-target-blocker diagnostics; `docs/SOLVER_ACCURACY_ENVELOPE.md` documents the boundary.
- Tests added: lifecycle command adapter tests, layout binding command tests, KLayout current-layout adapter boundary test, KLayout session editor shell region-render test, KLayout session path adapter tests, KLayout capture adapter boundary split tests, artifact generator handler tests, external-mode editor policy tests, report artifact repair tests, layout crop repair service tests, KLayout layout crop exporter tests, visual process artifact generator tests, setup-guide card model tests, KLayout setup-guide shell tests, diagnostics dashboard tests, process-flow mode policy tests, dense overview golden tests, recipe path adapter command tests, setup-guide recipe picker tests, KLayout recipe path adapter tests, standalone point capture tests, standalone line capture tests, standalone KLayout capture batch probes, live KLayout GUI capture-surface tests, solver accuracy envelope fixture tests, and etch depth/blocker diagnostic tests.
- Tests passing: `python -m unittest discover -s tests -t .` passed with 703 tests and 19 skipped tests. `python -m tools.release_check --include-klayout` also passed, including quality gates, ruff, mypy, static analysis, project health, unittest discovery, KLayout integration/process/UI lanes, compileall, and package build.
- Tests failing: none in the targeted stabilization lane.
- Known blockers: no unresolved P0/P1 stabilization blockers in the current contract. Remaining items are release polish, broader visual galleries, and future product-scope features.
- Next packet: no higher-priority stabilization packet remains; choose release polish or a new product feature packet intentionally.
- Architecture risks: artifact generators must register derived outputs through central `ArtifactRecord` updates and must not store loose filenames on capture or report records.

## What Works

- Process Planner sessions are now explicit editable `session.json` documents. `SessionDocument`
  tracks the loaded path, schema version, dirty state, revision, captures, artifacts, warnings, and
  workflow state while preserving unknown top-level fields where practical.
- `SessionDocumentLoader`, `SessionDocumentWriter`, `SessionMigrationService`,
  `SessionValidationService`, `SessionStore`, `ActiveSessionContext`, and
  `RecentSessionRegistry` provide the document lifecycle backbone for new/open/save/save-as/recent
  flows.
- New session creation immediately writes a valid minimal `session.json` and creates standard
  `artifacts`, `exports`, `images`, `drawings`, `reports`, and `process_outputs` folders.
- Opening a saved `session.json` now sets one clear active session context, records the recent
  session path, validates artifacts, adds non-blocking source-layout warnings, and opens the
  unified editor from the loaded document.
- Saving editor edits applies dirty metadata, updates the modified timestamp, validates the
  document, writes through temp/backup/atomic replace, clears dirty state, and keeps the loaded
  document path.
- The session editor now shows a no-active-session start screen with New Session, Open Existing
  Session JSON, and Open Recent actions instead of failing silently when no document is loaded.
- Top-level `New Session`, `Open Session`, `Open Recent Session`, and `Save Session As` commands
  now route through a fakeable `SessionPathAdapter`. KLayout registration supplies the Qt/KLayout
  path adapter, and cancel cases return structured non-mutating command results.
- `Bind Current Layout to Session` now routes through a fakeable `SessionLayoutAdapter`, updates and
  saves `SourceLayoutContext`, adds structured mismatch warnings, and replays durable
  `CanvasObject` overlays when an overlay manager is supplied. KLayout registration supplies the
  current-layout adapter and overlay backend.
- KLayout plugin registration now supplies a KLayout-backed session editor shell factory. The
  factory consumes the same header, navigator, preview, inspector, action, and status view-model
  regions as the in-memory shell, preserving callbacks through the command/dispatcher route.
- Built-in artifact repair now has concrete headless generator handlers for capture CSV export,
  SVG placeholder images, measurement annotation refresh, overview SVG regeneration, and
  process-output JSON regeneration/export, plus PowerPoint report-output repair and live layout
  crop repair when a KLayout exporter is injected. Generators that update owner refs or sibling
  artifacts return an explicit `ArtifactGenerationResult`, allowing the repair service to preserve
  canonical `SessionRecord` updates instead of replacing one artifact in isolation.
- Visual process artifacts now repair through role-specific generator selection. Profile,
  cross-section, full-stack compressed, point-stack, and process-flow records invoke the
  solver/render contract and write SVG image artifacts; generic process-output JSON export remains
  available for non-visual process-output artifacts.
- Artifact repair requests now verify that a selected generator has a concrete handler. Generator
  declarations without handlers produce a stable `GENERATOR_HANDLER_UNAVAILABLE` unavailable
  request and warning instead of surfacing a dead repair action.
- Generator-declared context requirements now participate in repair requests. Live-layout
  registrations such as `layout_crop` report `SOURCE_LAYOUT_REQUIRED_FOR_REPAIR` before falling
  through to `GENERATOR_HANDLER_UNAVAILABLE`, so repair queues show the first operator action
  required.
- Reporting Workbench output-folder selection now uses a `ReportOutputAdapter`. The in-memory
  workbench can choose a destination, persist it on `ReportRequest`, export to that folder, and
  KLayout registration supplies a Qt folder picker adapter without importing Qt in reporting code.
- Reporting Workbench stale-output readiness now has an explicit `regenerate_stale` action and
  primary button routing. Missing and stale report artifact repairs no longer share the same
  action label or service call.
- Mode registry now exposes explicit visible-catalog helpers. Legacy `cdsem_capture`, internal
  `process_aware_metrology`, and report-only `process_flow_summary` remain registered for saved
  sessions but are hidden from normal new-session pickers. KLayout mode selection uses the visible
  registry instead of raw enum values.
- App bootstrap now loads external JSON mode folders from `MPP_MODE_DEFINITION_DIRS` through the
  existing data-only mode loader. Diagnostics shows loaded external mode IDs and mode-load warnings.
  KLayout picker selection now accepts visible external registry IDs, and registered custom mode IDs
  round-trip through `SessionDocument` as durable `SessionModeId` strings. Editor builders and the
  default adapter consume the same injected registry, so external setup, measurement, dashboard, and
  metadata policy shapes generic view models without hard-coded built-in IDs. Unknown unregistered
  saved mode IDs still fall back to `simple_capture` with `unsupported_mode` warnings.
- Dirty close now blocks until save, discard, or cancel is chosen by the UI/controller caller.
- Canonical session records exist with schema `5.0.0`, central artifact registry records, captures, nested measurements, canvas objects, warnings, workflow state, setup, reports, process outputs, and raw-field preservation paths.
- Session JSON persistence loads older integer-schema payloads through migration, writes UTF-8 indented JSON, and has tests for round trip, unknown field preservation, missing artifacts, and canonical artifact refs.
- Persistent canvas objects support saved and pending site boxes, selection flags, active-parent flags, restore commands, stale/invalid styling, and fakeable overlay backends.
- The unified editor document model normalizes dashboard, setup, pending captures, saved captures, measurements, grid datasets, process outputs, reports, artifact-backed drawing previews, and warnings.
- Editor action dispatch routes save, CSV export, pending save/retake/discard, selection, canvas selection, and artifact regeneration through workflow services.
- The session editor controller now rerenders the active shell window after selection and mutating action callbacks, so navigator selection, preview rows, inspector fields, actions, and status text stay synchronized with the rebuilt `SessionDocument`.
- The session editor navigator now has transient search/warning filter state owned by the controller.
  Filtering preserves user-facing navigator groups, hides empty groups, rerenders modelessly through
  the shell callback, and is not stored in canonical session JSON.
- The session editor header/status presenter now surfaces session name, mode, output folder, setup state, capture state, selected item state, dirty state, warning count, and process-context state from the document/state-machine spine.
- The session editor header now exposes primary command-shaped actions for save, resume pending capture, reopen setup, attach/validate process context, export CSV, build report, open output folder, and close through the same `EditorAction` callback path as inspector actions.
- Session editor header actions now bridge to the shared `CommandRouter` for app-owned intents:
  `Save Edits` routes through `SaveSessionEdits` before delegating to the editor dispatcher,
  `Reopen Setup` opens the setup guide for the active editor session, and `Close` routes through
  `EndActiveSession` so pending/dirty blockers surface inline and diagnostics record the command.
- `WindowRegistry` now exposes named modeless product-surface methods for the session editor,
  setup guide, recipe editor, and diagnostics panel. Controllers use those methods instead of
  hand-owning duplicate window keys, while the registry still delegates lifecycle work to a
  fakeable toolkit backend.
- Active editor commands now also cover selected-item workflows through the same bridge:
  pending save/retake/discard, composite save/retake, add/save/retake/discard measurement,
  regenerate artifact, regenerate process output, and discard unsaved edits all route through
  `CommandRouter` before delegating to the editor dispatcher.
- Editor export and shell-handoff actions now have app command IDs too. `ExportCSV` and
  `OpenOutputFolder` route through `CommandRouter`, delegate to the editor dispatcher, and preserve
  returned output paths on `CommandRouteResult.output_path` for UI adapters.
- Process-context editor commands now use the same bridge for attach, detach, validate, and
  regenerate process output. Payload-bearing editor actions such as attach-recipe with a selected
  recipe path preserve their payload while still routing through `CommandRouter`; direct attach
  commands without a path return structured unavailable results.
- The required `TakeAnotherMeasurement` command now applies the existing post-measurement
  completion workflow to the active editor document, reselects the parent capture, rearms the
  measurement line primitive, and returns structured unavailable results when no saved measurement
  is available.
- `Open Output Folder` now returns a typed modeless path handoff through `EditorActionResult.output_path` when session paths are configured; workflow code does not launch an external file browser directly, and missing paths return a structured unavailable result.
- Generic capture start/cancel commands now route through a shared app-level capture command service. `StartCapture`, `StartBoxCapture`, `StartLineCapture`, `StartPointCapture`, and `CancelCapture` update durable workflow arming state, reuse `CanvasInteractionEngine`, refresh the active editor document, and mirror active setup-guide session state when both surfaces inspect the same session.
- `EndActiveSession` now routes through a modeless session lifecycle service. It closes and clears safe editor/setup/diagnostics session surfaces and capture arming, while dirty editor edits or pending capture review items return structured blocked command results instead of silently closing or doing nothing.
- The modeless setup guide now attaches action callbacks to its shell window and routes setup-stage commands through the shared `CommandRouter`. Setup capture commands arm shared canvas primitives and durable workflow state, setup-state commands update canonical setup fields, optional explicit setup stages can be skipped without prompts, recipe-context validation persists structured warnings, implemented modeless actions such as close update the shared `WindowRegistry`, and still-deferred setup actions return structured unavailable results.
- Setup-guide cards now have host-ready `SetupStageCardModel` rows with status tone, requirement
  badge, artifact badge, warning badge, action label, disabled reason, and active-state metadata.
  KLayout plugin registration injects a `KLayoutSetupGuideSurfaceFactory` through
  `ModelessSurfaceShell`, so the production setup guide consumes view models without workflow/Qt
  coupling.
- Setup guide cards now preserve command labels, enabled state, and disabled reasons through
  `SetupActionViewModel` rows for primary, secondary, and footer actions, so widgets can render
  card buttons directly from the presenter without inferring labels or prompt logic.
- Setup guide stage cards now expose explicit `requirement_badge` and `artifact_badge` fields.
  Required/optional state is derived from setup policy/state, and setup-item artifact references
  summarize central registry status as present, missing, stale, failed, mixed, or none.
- Rendering and annotation pipelines use editable scene specs, SVG as canonical output, optional rasterizer injection, drawing persistence, and editor/render bridge refresh hooks.
- Drawing export now returns canonical `ArtifactRecord` sets directly; capture, measurement, and process-owned drawings update the central registry plus owner `artifact_refs` without mirrored image/drawing wrappers.
- Canvas pending-crop artifacts are now created, promoted, or removed explicitly by workflow commands rather than synthesized during `SessionRecord` construction.
- Repeated measurement annotation refresh failures upsert one failed SVG artifact record with stable warning IDs and repair metadata, and preview options surface the `regenerate_artifact` repair action.
- Diagnostics and traceability services expose command, workflow, seam, artifact, warning, and snapshot views through pure Python services.
- Advanced Diagnostics now opens a fakeable shell summary plus a structured dashboard with active
  session, session path, dirty state, loaded/built-in modes, mode-validation fallback state,
  durable workflow state, armed capture primitive, selected editor item, selected canvas object,
  recipe-context state, solver/render backend state, report readiness, artifact-repair state,
  artifact status counts, warning codes, missing artifact count, recent command names, recent
  failure summaries, open windows, actions, and recent diagnostic events.
- Advanced Diagnostics actions now render as typed `EditorActionViewModel` rows for exporting a
  diagnostics bundle, copying command trace, opening the session folder, scanning artifacts,
  validating the session, and validating modes. Actions carry disabled reasons when no trace or
  session folder is available.
- Advanced Diagnostics actions now dispatch through a typed controller service. Shells receive a
  generic action callback, action attempts emit diagnostics events, command-trace/folder/export/
  validation actions return structured modeless results, and action failures are captured as
  exception diagnostics instead of escaping from widget callbacks.
- Explicit pure UI state-machine evaluators now summarize session UI, capture interaction, pending review, measurement workflow, recipe context, and artifact repair state for editor headers, diagnostics, and future Qt widgets.
- Built-in workflow modes are represented by declarative `ModeDefinition` records in a pure `ModeRegistry`; definitions now use typed policy blocks for capabilities, setup, capture, metadata, measurements, artifacts, process, editor, and reporting. External JSON mode definition folders can be loaded as inert data, and diagnostics reads loaded modes from the registry.
- Profilometry Planner and Ellipsometry Planner are now registered as declarative process-aware compound modes. Their built-in definitions live separately from the registry contract, and the shared workflow supports site-then-line and site-then-point pending composites.
- Profilometry Planner and Ellipsometry Planner declare setup behavior, editor preview/action IDs, and reporting section stubs as mode policy data in addition to capture, metadata, process, and artifact policies.
- Pending composite review now uses unified editor actions: Save Composite, Retake Line/Point, Retake Site Box, Discard Composite, and Exit. These dispatch to shared compound workflow services, not mode-specific review windows.
- Compound review service calls now use typed command contracts for retake parent, retake inner feature, discard, and exit, matching the save-command boundary already used by the editor.
- Editor document selection now indexes parent and child canvas objects for pending and saved composite captures. Saved composite captures also expose child feature items, so selecting the capture highlights the full parent+feature overlay set while selecting the feature highlights only the line/point child overlay.
- Saved profilometry and ellipsometry composites now have document-store reload coverage for parent/child canvas indexes, feature item indexes, artifact refs, warning refs, and `process_context.active` extension refs.
- Recipe/process context commands now attach, detach, validate, refresh fingerprints, and expose regeneration hooks through editor actions. Canonical JSON writes the process context as `process_context.active`, while flat process-context payloads are migration-only. Missing recipe/solver states become structured warnings instead of capture-save failures.
- Recipe editor process-step cards now expose explicit enabled/disabled status labels and
  command-shaped card actions for duplicate, delete, move, enable/disable, and preview-through-step.
  The selected step detail panel uses the same shared action policy, so card and detail widgets do
  not drift.
- Process-context validation now checks missing recipes, missing recipe files, missing solver backends, missing render profiles, stale process-output records/artifacts, and process-aware captures missing the `process_context.active` reference.
- The dashboard now exposes session-level `Regenerate Process Outputs`, routing through the all-process-aware-captures regeneration path.
- Process-aware capture inspector metadata now includes recipe, solver operation, process window, per-capture process-output status counts, and warning count from canonical session records.
- Process warning items now expose repair actions through the generic editor adapter: attach recipe, validate process context, regenerate the owning capture's process output, open recipe file when a path exists, and ignore warning. Ignore updates durable `WarningRecord.status` instead of deleting the canonical warning.
- The dashboard process-context fields now derive recipe missing/mismatch, solver unavailable, and warning-count states from open structured `WarningRecord` codes. The open-recipe action returns a typed path handoff to the UI shell when the file exists.
- Process-output editor items are now first-class document items with solver summary metadata, capture ownership, process-output artifact previews, and a regenerate action that routes back to the owning capture instead of treating the output ID as a capture ID.
- Process-aware validation, inspector metadata, and regeneration target discovery now use structural process-extension detection, so custom mode namespaces such as `fib_process` are supported without adding built-in extension-name branches.
- Pending composite review metadata now consumes mode-declared field IDs from `ModeDefinition.metadata.field_ids()`, so profilometry line settings and ellipsometry point/film fields render through the shared editor adapter.
- Built-in profilometry/ellipsometry compound capture requests now come from `ModeWorkflowPlanner`, which maps mode capture/process policy into the shared compound capture request model.
- Shared line and point capture routing now resolves active compound child steps through mode policy, including custom/namespaced mode definitions in tests, instead of hard-coded built-in mode checks.
- Compound child canvas object types now come from mode capture policy, so custom line-based modes can persist non-profilometry child overlays such as `fib_cut`.
- Compound child display labels now come from mode capture policy and are persisted on feature payloads, so pending/saved editor actions use custom labels such as `FIB Cut`.
- Saved profilometry extensions now use `line_feature_id` and include empty `outputs.stack_change_windows` / `outputs.step_heights`; saved ellipsometry extensions use `point_feature_id` and an empty `point_stack`.
- Compound capture save now creates all process-aware placeholder artifact roles declared by the built-in modes, including `full_stack_compressed_image` and `film_thickness_summary`.
- Process-output regeneration now calls `HybridCrossSectionSolver` for process-aware saved captures when an attached recipe is available. Solver summaries are stored on canonical `ProcessOutputRecord` records, and a configured editor dispatcher writes JSON process-output artifacts through `ProcessOutputStore` while updating central artifact records to `present`.
- Canonical artifact ID generation now lives in a registry-focused helper module; legacy artifact conversion is isolated to migration inputs.
- Legacy `capture_type` is translated at integer-schema migration only; v5 capture records and generated capture CSV artifacts use canonical `type`.
- Saved profilometry and ellipsometry captures expose mode-appropriate action labels through a shared saved-capture action policy: replace site box, replace line/point, regenerate line/point annotation, process-context actions, and regenerate process output/point stack.
- The editor dashboard now summarizes process outputs from canonical `ProcessOutputRecord.status` counts.
- Built-in quality gates, ruff, mypy, static analysis, unit discovery, live KLayout batch/process/UI
  lanes, and release packaging are currently passing through
  `python -m tools.release_check --include-klayout`.
- Integration audit documents now cover seam ownership, object contracts, dependency direction,
  end-to-end workflow evidence, no-bypass findings, known limitations, and risk-ranked next
  priorities.
- Command identifiers are now owned by a pure domain command contract and re-exported by the app
  layer, removing the workflow-to-app dependency that import-linter flagged during the integration
  audit.
- Dependency direction now has both import-linter coverage and an AST-based integration test under
  `tests/integration/dependency`.
- Saved capture to child measurement line now has a pure workflow slice:
  - `ADD_MEASUREMENT` marks the selected capture's canvas object as active parent.
  - Shift-drag line capture creates a pending nested `MeasurementRecord`.
  - The line canvas object persists under the parent canvas object.
  - Pending measurement items expose Save Measurement, Retake Measurement Line, Discard
    Measurement, and Return to Parent Capture through the generic editor adapter.
  - `SAVE_EDITS` applies measurement metadata, promotes pending measurements to saved, and refreshes measurement-owned annotation drawing artifacts through the existing render bridge.
  - Reload through `SessionDocumentStore` restores the parent capture item, child measurement item, and both canvas objects.
  - `REGENERATE_ARTIFACT` can refresh a selected measurement's annotation artifact after the initial save.
  - The save result now carries the one allowed post-measurement prompt with `Take Another
    Measurement`, `Return to Editor`, and `Done` choices; a pure workflow applies those choices.

## Scope-Limited / Polish

- Menu commands for `New Session...`, `Open Session...`, `Open Recent`, `Save Session As`, and
  `Bind Current Layout to Session` route through fakeable adapters, with KLayout-backed adapters
  supplied at plugin registration. `Repair Session` and `Import Legacy Session Folder` remain
  separate future workflows when scoped.
- Canvas overlay restore is document-backed through durable canvas objects and editor indexes.
  Live KLayout view rebinding is command-backed; manual dialog smoke remains a release checklist
  item.
- KLayout integration remains intentionally thin; normalized line measurement gestures, profilometry child-line gestures, ellipsometry child-point gestures, standalone point gestures, and standalone line gestures route through shared capture tools, plus opt-in live KLayout batch smokes that verify a real `pya.Layout` is not mutated.
- Measurement annotation artifact generation now produces editable spec/SVG/PNG outputs when a render bridge and rasterizer are available; export/rasterizer failures become structured warning or error results with retry-safe repair metadata.
- Artifact generator repair is executable for the P1 stabilization paths. CSV, placeholder SVG,
  measurement annotation, overview SVG, process-output JSON, PowerPoint report-output,
  KLayout-injected live layout-crop, and visual process SVG handlers are registered where their
  required adapters are available.
  Live layout-dependent declarations now expose source-layout requirements before exporter/handler
  gaps.
- Reporting export is headless, destination-selectable, centrally registered, and repairable for
  generated PowerPoint report outputs. Remaining report UX polish is mostly production shell
  presentation and broader output-format repair coverage.
- `fib_cut_planner` is intentionally not added in this stabilization pass. It remains descoped from
  the visible catalog until it can be implemented as a complete declarative mode with tests.
- External mode discovery is diagnostics-visible, loaded custom external mode IDs are selectable for
  new sessions through the KLayout picker, and generic editor behavior is shaped by the declarative
  policy blocks supplied by the loaded `ModeDefinition`.
- Editor shell is minimal and generic; it renders view models but is not a polished production editor.
- Armed capture status now has a shared presenter from durable workflow state to a
  `CaptureToolStatusViewModel`; the session editor status strip and setup guide view model
  consume the same non-blocking gesture guidance, while final Qt banner styling remains polish.
- Editor actions now carry disabled reasons. Deferred report-building actions are rendered as
  disabled with clear reasons, and dispatching them returns structured unavailable results.
- Mode definitions and validation exist in tests and UI shell contracts; unknown saved mode IDs now load through a safe fallback with warning/audit records and original mode preservation in extensions. External custom-mode JSON loading exists, while app/release configuration for discovering installed mode folders remains future work.
- Diagnostics identify seams, warning states, selected editor/canvas state, mode fallback state,
  recent failures, and grouped dashboard sections; live visual dashboard polish remains useful.
- KLayout integration includes a pure capture gesture adapter that routes normalized Shift-drag measurement/profile/standalone line events, standalone Shift-click point events, and Shift-click ellipsometry point events into shared workflow services and restores marker overlays without importing `pya` or mutating source layout data; the live KLayout batch lane passes with `KLAYOUT_EXE=C:\Users\edmun\AppData\Roaming\KLayout\klayout_app.exe`.
- Standalone point capture is implemented as a pending-capture workflow: armed Shift-click creates canonical point geometry, KLayout boundary routing updates overlays, and pending review promotes the point into a saved capture record.
- Standalone line capture is implemented as a pending-capture workflow: parentless Shift-drag creates canonical line geometry, KLayout boundary routing updates overlays, and pending review promotes the line into a saved capture record.
- Ellipsometry point capture remains wired for the process-aware site-then-point child step in pure tooling, KLayout-boundary tests, and the opt-in live KLayout batch probe.
- Process output regeneration is solver-backed for attached recipes, exporter-backed for JSON summary artifacts when paths are configured, and warning-only for missing recipe, unavailable solver, parse failure, solver failure, or artifact export failure paths.
- Recipe editor card/header actions now route through a pure dispatcher. It supports safe
  in-memory card selection, validation, and add-step templates, while save/open/attach remain
  structured unavailable command results until real recipe persistence workflows are wired.
- The modeless recipe editor window now exposes an action callback for header/card actions. Recipe
  edits dispatch through `RecipeEditorActionDispatcher` and refresh the existing window; Close is a
  modeless controller action that updates the shared `WindowRegistry`.
- Recipe editor header state now renders through `RecipeHeaderViewModel`, including recipe path,
  dirty state, validation status, warning count, and attachment readiness. Header actions expose
  disabled reasons for unloaded, unsaved, or dirty recipes instead of leaving shell widgets to infer
  save/attach availability.
- Dirty recipe-editor close now returns a structured blocked result and leaves the modeless window
  open. The explicit `CloseRecipeEditor:discard` action is the confirm-discard path for future UI
  confirmation widgets.
- `SaveRecipe` now routes through the modeless recipe editor controller and
  `ProcessRecipeJsonStore`. Recipes with `metadata.recipe_path` are written as indented JSON with
  atomic temp/replace and backup behavior; save failures return structured error results while
  preserving dirty in-memory edits.
- `SaveRecipeAs:<path>` uses the same modeless save service, writes the recipe to the supplied
  path, records `metadata.recipe_path`, clears dirty state on success, and returns a structured
  unavailable result when no path is supplied.
- `NewRecipe`, `NewRecipe:discard`, `OpenRecipe:<path>`, and `OpenRecipe:discard:<path>` now route
  through modeless controller helpers. New/open blocks on dirty recipes until discard is explicitly
  confirmed, and opened recipes record `metadata.recipe_path`.
- Recipe editor view models now include a selected-card detail panel for materials, steps, and
  layer references. Material details expose category/color/visibility/notes fields and material
  actions; step details expose operation/material/mask/thickness/notes fields and step actions.
- Recipe material deletion is now an inline, modeless action. Unused materials are removed from
  the in-memory recipe and mark it dirty; materials referenced by process steps return a structured
  blocked result with warning IDs and repair guidance instead of prompting or silently deleting.
- Recipe material tab/detail actions now use command IDs for add, duplicate, delete, visibility
  toggle, and usage lookup. Add/duplicate/toggle mutate the in-memory recipe and mark it dirty;
  usage lookup returns an inline step list without dirtying the recipe.
- Recipe process-step detail actions now support modeless duplicate, delete, move up/down,
  enable, and disable behavior through structured dispatcher results. Step reordering blocks at
  list boundaries with inline guidance instead of doing nothing.
- Post-measurement completion is represented as an explicit prompt result and pure workflow
  choice handler; final Qt prompt rendering remains deferred.

## Tests In Place

- Session document lifecycle tests cover new session JSON creation, open existing JSON, loaded-path
  tracking, recent-session tracking, atomic save/backup, unknown-field preservation, save-as,
  dirty-close blocking, missing source-layout warnings, invalid JSON errors, and no-session editor
  start-screen behavior.
- Session JSON, canonical registry, migration, unknown field preservation, missing artifact repair, and CSV/session round trip.
- Registry-first tests now assert explicit canonical owner refs and artifact records rather than hydrated capture image/drawing compatibility fields.
- Canvas session models, canvas interaction, overlay restore/selection, and pending capture lifecycle.
- Unified editor document building, store/dispatcher actions, shell controller, and render bridge failure handling.
- Session editor command-bridge tests covering primary header `Save Edits`, `Reopen Setup`, and
  `Close` routing through `CommandRouter`, active-session setup guide handoff, successful
  command-backed session save, direct no-active-session save handling, successful end-session
  close, and blocked pending-review close behavior.
- Session editor selected-item command tests cover inspector pending-save routing through
  `SavePendingCapture`, direct `AddMeasurement` dispatch from the selected capture, and
  `DiscardUnsavedEdits` dirty-state cleanup.
- Session editor process-command bridge tests cover attach-recipe payload preservation through
  `CommandRouter`, plus direct validate/detach commands against the active editor document.
- Session editor completion-command tests cover `TakeAnotherMeasurement` rearming the same parent
  capture from the active editor document and the no-saved-measurement unavailable result.
- Session editor export-command tests cover primary-action `ExportCSV` routing, output-folder path
  handoff, and no-active-document unavailable handling.
- Session editor dispatcher tests covering `Open Output Folder` path handoff and no-session-folder
  unavailable behavior.
- Rendering pipelines, drawing persistence, SVG output, and fake rasterizer export paths.
- UI command routing and KLayout boundary/import isolation.
- Hybrid process solver pure fixtures, although solver integration is not the current alpha priority.
- New child-measurement workflow tests covering active-parent line capture, pending measurement
  review actions, retake/discard transitions, full measurement metadata edits, annotation artifact
  generation/regeneration, save/reload restoration, and render failure paths.
- Point and line capture tests covering normal-navigation preservation, standalone pending point/line capture, KLayout standalone point/line routing, saved point/line promotion, parented measurement lines, and ellipsometry child-point capture.
- Mode validation tests covering unknown v5 and legacy mode IDs loading through graceful fallback instead of crashing.
- Mode registry tests covering built-in registration, capability definitions, duplicate detection, and invalid custom definitions as warnings.
- Mode registry tests assert process-aware setup, editor preview/action, and reporting policy declarations.
- Compound capture workflow tests covering profilometry site-plus-line and ellipsometry site-plus-point saves, central artifact placeholders, warning generation, workflow arming, and child geometry validation.
- Compound mode routing tests cover active workflow routing from declarative mode policy, including a namespaced custom `site_then_line` mode with its own child canvas object type and editor action labels.
- Compound editor review tests covering composite action labels, presenter output, save, retake inner feature, retake parent site box, discard, exit, parent+child canvas selection indexes, and child feature item selection.
- Compound session reload tests cover saved profilometry and ellipsometry composites through `SessionDocumentStore` save/load.
- Process context workflow tests covering recipe attach, missing paths, fingerprint mismatch warnings, detach/validate state, regeneration warnings, editor dispatcher routing, and dashboard/capture actions.
- Warning repair action tests covering process warning action derivation, recipe-file open payloads, capture-targeted regeneration, and durable ignored-warning status.
- Process dashboard status tests covering warning-derived recipe/solver states and open process warning counts.
- Process context workflow and regeneration tests cover custom process-aware extension namespaces that are not profilometry or ellipsometry.
- Process context validation tests cover render-profile warnings, stale output warnings, stale artifact warnings, and capture process-context reference warnings.
- Dashboard process-output action tests cover all-capture regeneration from the process-context dashboard.
- Process-aware capture metadata tests cover recipe, solver operation, process window, output status, and warning fields.
- Compound mode metadata tests cover declaration-driven pending review fields and reviewed metadata preservation on composite save.
- Compound process artifact shape tests cover full built-in placeholder role declarations, central artifact records, and mode-specific saved extension keys.
- Compound review command tests cover typed retake, discard, and exit command contracts.
- Saved composite action tests cover profilometry/ellipsometry labels and explicit unavailable results for deferred replace workflows.
- Legacy capture migration-boundary tests assert old field translation stays outside canonical v5 capture record loading.
- Process-output regeneration tests covering solver-backed profilometry regeneration, editor dispatch, canonical output metadata, JSON artifact export, artifact status transitions, export failure warnings, and explicit solver-unavailable warnings.
- Process-output editor item tests covering solver summary fields, process-output-only previews, and output-item regeneration routing.
- Diagnostics summary tests covering active session, mode list, mode validation, editor/canvas selection, artifact status counts, warning codes, recent failures, and recent command/event visibility.
- Diagnostics dashboard tests covering grouped required rows, session path, dirty state,
  solver/render backend rows, report readiness, recent commands, and shell action models.
- UI state-machine tests covering pending review, armed capture, live preview, child pending capture review, pending measurement review, recipe warnings, artifact repair tasks, and active workflow resume state.
- Capture status presenter tests covering session-derived box/line/point guidance, setup-guide
  propagation, editor status-strip precedence, unknown primitive handling, and mode-specific
  point/line gesture hints.
- Recipe editor action tests covering command normalization, in-memory card selection, add-step
  template dirty state, modeless controller refresh, validation warning IDs, and deferred save
  actions returning structured unavailable results.
- Recipe editor callback tests covering modeless window action dispatch and close behavior through
  the window registry.
- Recipe editor dirty-close tests covering blocked close and confirmed discard close behavior.
- Recipe editor opening tests covering new recipe, path-backed open, dirty-switch blocking,
  discard-confirmed switching, missing paths, and bad files.
- Recipe editor session-attachment tests covering saved-recipe attachment into the active
  session process context, dirty-recipe blocking, and no-active-session unavailable results.
- Recipe editor card tests covering selected material and process-step detail-panel fields and
  actions.
- Recipe editor validation-card tests covering related-card links and dispatchable selection
  actions for inline validation rows.
- Recipe editor action tests covering blocked deletion of used materials and safe in-memory deletion
  of unused materials.
- Recipe editor material-action tests covering add, duplicate, visibility toggle, and usage lookup.
- Recipe editor material-edit tests covering command-routed edits for material name, category,
  notes, selected-card preservation, dirty state, and malformed payload errors.
- Recipe editor step-action tests covering duplicate, move, disable, blocked boundary moves, and
  command-routed edits for common process-step fields.
- Recipe editor preview-action tests covering full-recipe preview scope, preview-through-step
  selection, missing-step errors, and backend-unavailable warning results.
- Modeless setup-guide controller tests covering shared-window reuse, command-router action
  callbacks, structured unavailable setup actions, and close behavior through the window registry.
- Setup-guide card and KLayout shell tests covering required/optional/blocked/skipped status badge
  models plus Qt-backed stage-card region rendering.
- Generic capture command tests covering default box arming, explicit box/line/point arming,
  selected-canvas parent propagation, setup-guide session mirroring, cancel/disarm, and structured
  no-active-session errors through `CommandRouter`.
- Session lifecycle command tests covering clean active-session close, pending-review blocking,
  dirty-editor blocking, modeless surface cleanup, capture disarm, and warning-level diagnostics for
  blocked end-session commands.
- Setup guide command tests covering origin point arming, alignment box arming, capture-status
  refresh, coordinate-mode updates, optional explicit stage skip, recipe-context validation
  warnings, setup-ready updates, and workflow disarming.
- Measurement completion prompt tests covering save-result prompt choices, rearming the same
  parent capture for another measurement, returning to the parent capture, and completing on the
  saved measurement.
- Disabled action tests covering header actions, adapter actions, pending-review button models,
  and dispatcher results for unavailable report generation.
- Measurement annotation repair tests covering repeated export failures, failed artifact status, repair metadata, stable warning IDs, and preview repair actions.
- Built-in artifact generator handler tests cover stale CSV rebuild, placeholder SVG write,
  measurement annotation regeneration, missing overview SVG repair, process-output JSON repair,
  missing-recipe unavailable repair, and no-handler unavailable repair through
  `ArtifactRepairService`.
- Layout generator requirement tests cover live-layout registration metadata and the transition
  from `SOURCE_LAYOUT_REQUIRED_FOR_REPAIR` to `GENERATOR_HANDLER_UNAVAILABLE` once a source layout
  is bound.
- Reporting Workbench output adapter tests cover choosing an output folder, cancel behavior, export
  into the selected destination, and KLayout folder-picker adapter wiring.
- Reporting Workbench repair tests cover missing and stale artifact regeneration routing plus stale
  readiness primary-action presentation.
- Layout crop repair tests cover adapter-backed crop export, capture-bounds metadata, selected
  artifact repair routing, and KLayout active-view export boundaries.
- Visual process artifact generator tests cover profile and cross-section SVG repair, role-specific
  generator selection, render metadata, and ready process-output synchronization.
- Mode catalog tests cover visible-mode IDs, hidden legacy/internal modes, and KLayout picker
  rejection of hidden legacy mode choices.
- Mode registry configuration tests cover environment-configured folders, accumulated load
  warnings, diagnostics visibility, registered custom mode ID round trips, and safe fallback for
  unregistered mode IDs.
- Opt-in KLayout batch smoke coverage for `KLayoutCaptureGestureAdapter` inside a real `pya` runtime, including saved measurement line, profilometry compound child-line capture, ellipsometry compound child-point capture, standalone point capture, and standalone line capture, gated by `MPP_RUN_KLAYOUT_TESTS=1`; current opt-in inventory is 10 live KLayout integration tests.
- Opt-in KLayout GUI automation covers real menu registration, main-window snapshot probes, modeless command-surface routing, and capture-surface contract probes through `MPP_RUN_KLAYOUT_UI_TESTS=1`, `klayout_app.exe`, and GUI `-e -rm` execution; current evidence is 4 passing live KLayout UI automation tests.

## Tests Still Needed

- UI adapter tests for actual file-picker driven New/Open/Save As commands.
- Live KLayout UI tests for `Bind Current Layout to Session` and delayed overlay restoration after
  binding a compatible layout/view.
- Legacy folder import recovery tests once the scanner is implemented beyond the command stub.
- Broaden opt-in live KLayout smoke coverage beyond batch probes if a stable GUI automation lane becomes available.
- Recipe file open workflow tests once file-picking paths are wired behind commands.

## Safe Reuse Points

- Keep using `SessionDocumentBuilder`, `EditorActionDispatcher`, `CanvasInteractionEngine`, and `CanvasOverlayManager` as the main editor/canvas seams.
- Keep artifact status and repair visibility in `ArtifactRecord` and `WarningRecord`.
- Keep KLayout/Qt code behind infrastructure and UI adapters.
- Package organization migration has progressed past temporary file-level shims: diagnostics now
  lives under `metrology_process_planner.diagnostics`, solver internals now live under
  `metrology_process_planner.solver`, and deleted old import paths are forbidden by
  `tools.audit_imports`.
- Architecture docs now live in `docs/FILE_ORGANIZATION_AUDIT.md` and
  `docs/PACKAGE_ARCHITECTURE.md`; import boundary smoke tests live under
  `tests/unit/architecture/`.
- Corrective domain migration moved the real artifact, capture, measurement, mode, and warning
  implementation modules into `domains/artifacts`, `domains/capture`, `domains/measurement`,
  `domains/modes`, and `domains/warnings`; the old session/flat shim files have been removed.
- `docs/COMPATIBILITY_SHIM_AUDIT.md` inventories removed shims, and `docs/CANONICAL_IMPORTS.md`
  documents canonical import locations for future work.
- `tools/audit_imports.py` now reports deprecated imports with canonical replacements, `pya`
  outside KLayout infrastructure, solver runtime imports, and domain runtime imports.

## Do Not Touch Yet

- Do not fork mode-specific editor dialogs for measurement review.
- Do not add KLayout shape mutation for overlays.
- Do not replace canonical session JSON or move canonical state into UI widgets.
- Do not integrate the process solver into alpha capture workflows until capture/editor persistence is steadier.

## Visual Review Status

- Added `tools/generate_visual_quality_gallery.py` for the reviewed gallery at
  `tests/output/visual_review_gallery/`.
- Added machine-readable `manifest.json` and `visual_issues.json` outputs.
- Added structural visual QA checks in
  `metrology_process_planner.testing.visual_quality`.
- Fixed cross-section SVG output so label extents stay in bounds and legends,
  scale bars, compression notes, and thin-layer notes are rendered.
- Added regression coverage in `tests/test_visual_quality_gallery.py`.
