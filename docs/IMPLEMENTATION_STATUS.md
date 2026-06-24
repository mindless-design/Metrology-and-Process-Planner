# Process Planner Implementation Status

Last updated: 2026-06-24

## What Works

- Canonical session records exist with schema `5.0.0`, central artifact registry records, captures, nested measurements, canvas objects, warnings, workflow state, setup, reports, process outputs, and raw-field preservation paths.
- Session JSON persistence loads older integer-schema payloads through migration, writes UTF-8 indented JSON, and has tests for round trip, unknown field preservation, missing artifacts, and canonical artifact refs.
- Persistent canvas objects support saved and pending site boxes, selection flags, active-parent flags, restore commands, stale/invalid styling, and fakeable overlay backends.
- The unified editor document model normalizes dashboard, setup, pending captures, saved captures, measurements, grid datasets, process outputs, reports, artifact-backed drawing previews, and warnings.
- Editor action dispatch routes save, CSV export, pending save/retake/discard, selection, canvas selection, and artifact regeneration through workflow services.
- The session editor controller now rerenders the active shell window after selection and mutating action callbacks, so navigator selection, preview rows, inspector fields, actions, and status text stay synchronized with the rebuilt `SessionDocument`.
- The session editor header/status presenter now surfaces session name, mode, output folder, setup state, capture state, selected item state, dirty state, warning count, and process-context state from the document/state-machine spine.
- The session editor header now exposes primary command-shaped actions for save, resume pending capture, reopen setup, attach/validate process context, export CSV, build report, open output folder, and close through the same `EditorAction` callback path as inspector actions.
- Session editor header actions now bridge to the shared `CommandRouter` for app-owned intents:
  `Save Edits` routes through `SaveSessionEdits` before delegating to the editor dispatcher,
  `Reopen Setup` opens the setup guide for the active editor session, and `Close` routes through
  `EndActiveSession` so pending/dirty blockers surface inline and diagnostics record the command.
- Active editor commands now also cover selected-item workflows through the same bridge:
  pending save/retake/discard, composite save/retake, add/save/retake/discard measurement,
  regenerate artifact, regenerate process output, and discard unsaved edits all route through
  `CommandRouter` before delegating to the editor dispatcher.
- `Open Output Folder` now returns a typed modeless path handoff through `EditorActionResult.output_path` when session paths are configured; workflow code does not launch an external file browser directly, and missing paths return a structured unavailable result.
- Generic capture start/cancel commands now route through a shared app-level capture command service. `StartCapture`, `StartBoxCapture`, `StartLineCapture`, `StartPointCapture`, and `CancelCapture` update durable workflow arming state, reuse `CanvasInteractionEngine`, refresh the active editor document, and mirror active setup-guide session state when both surfaces inspect the same session.
- `EndActiveSession` now routes through a modeless session lifecycle service. It closes and clears safe editor/setup/diagnostics session surfaces and capture arming, while dirty editor edits or pending capture review items return structured blocked command results instead of silently closing or doing nothing.
- The modeless setup guide now attaches action callbacks to its shell window and routes setup-stage commands through the shared `CommandRouter`. Setup capture commands arm shared canvas primitives and durable workflow state, setup-state commands update canonical setup fields, optional explicit setup stages can be skipped without prompts, recipe-context validation persists structured warnings, implemented modeless actions such as close update the shared `WindowRegistry`, and still-deferred setup actions return structured unavailable results.
- Rendering and annotation pipelines use editable scene specs, SVG as canonical output, optional rasterizer injection, drawing persistence, and editor/render bridge refresh hooks.
- Drawing export now returns canonical `ArtifactRecord` sets directly; capture, measurement, and process-owned drawings update the central registry plus owner `artifact_refs` without mirrored image/drawing wrappers.
- Canvas pending-crop artifacts are now created, promoted, or removed explicitly by workflow commands rather than synthesized during `SessionRecord` construction.
- Repeated measurement annotation refresh failures upsert one failed SVG artifact record with stable warning IDs and repair metadata, and preview options surface the `regenerate_artifact` repair action.
- Diagnostics and traceability services expose command, workflow, seam, artifact, warning, and snapshot views through pure Python services.
- Advanced Diagnostics now opens a fakeable shell summary with active session, loaded/built-in modes, mode-validation fallback state, durable workflow state, armed capture primitive, selected editor item, selected canvas object, recipe-context state, artifact-repair state, artifact status counts, warning codes, missing artifact count, recent command names, recent failure summaries, and recent diagnostic events.
- Explicit pure UI state-machine evaluators now summarize session UI, capture interaction, pending review, measurement workflow, recipe context, and artifact repair state for editor headers, diagnostics, and future Qt widgets.
- Built-in workflow modes are represented by declarative `ModeDefinition` records in a pure `ModeRegistry`; definitions now use typed policy blocks for capabilities, setup, capture, metadata, measurements, artifacts, process, editor, and reporting. External JSON mode definition folders can be loaded as inert data, and diagnostics reads loaded modes from the registry.
- Profilometry Planner and Ellipsometry Planner are now registered as declarative process-aware compound modes. Their built-in definitions live separately from the registry contract, and the shared workflow supports site-then-line and site-then-point pending composites.
- Profilometry Planner and Ellipsometry Planner declare setup behavior, editor preview/action IDs, and reporting section stubs as mode policy data in addition to capture, metadata, process, and artifact policies.
- Pending composite review now uses unified editor actions: Save Composite, Retake Line/Point, Retake Site Box, Discard Composite, and Exit. These dispatch to shared compound workflow services, not mode-specific review windows.
- Compound review service calls now use typed command contracts for retake parent, retake inner feature, discard, and exit, matching the save-command boundary already used by the editor.
- Editor document selection now indexes parent and child canvas objects for pending and saved composite captures. Saved composite captures also expose child feature items, so selecting the capture highlights the full parent+feature overlay set while selecting the feature highlights only the line/point child overlay.
- Saved profilometry and ellipsometry composites now have document-store reload coverage for parent/child canvas indexes, feature item indexes, artifact refs, warning refs, and `process_context.active` extension refs.
- Recipe/process context commands now attach, detach, validate, refresh fingerprints, and expose regeneration hooks through editor actions. Canonical JSON writes the process context as `process_context.active`, while flat process-context payloads are migration-only. Missing recipe/solver states become structured warnings instead of capture-save failures.
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
- Built-in quality gates, ruff, mypy, and unit discovery are currently passing.
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

## Partially Implemented

- KLayout integration remains intentionally thin; normalized line measurement gestures, profilometry child-line gestures, and ellipsometry child-point gestures route through shared capture tools, plus opt-in live KLayout batch smokes that verify a real `pya.Layout` is not mutated.
- Measurement annotation artifact generation now produces editable spec/SVG/PNG outputs when a render bridge and rasterizer are available; export/rasterizer failures become structured warning or error results with retry-safe repair metadata.
- Editor shell is minimal and generic; it renders view models but is not a polished production editor.
- Armed capture status now has a shared presenter from durable workflow state to a
  `CaptureToolStatusViewModel`; the session editor status strip and setup guide view model
  consume the same non-blocking gesture guidance, while final Qt banner styling remains polish.
- Editor actions now carry disabled reasons. Deferred report-building actions are rendered as
  disabled with clear reasons, and dispatching them returns structured unavailable results.
- Mode definitions and validation exist in tests and UI shell contracts; unknown saved mode IDs now load through a safe fallback with warning/audit records and original mode preservation in extensions. External custom-mode JSON loading exists, while app/release configuration for discovering installed mode folders remains future work.
- Diagnostics identify seams, warning states, selected editor/canvas state, mode fallback state, and recent failures, but they are not yet a polished end-user troubleshooting dashboard.
- KLayout integration includes a pure capture gesture adapter that routes normalized Shift-drag line events and Shift-click ellipsometry point events into shared workflow services and restores marker overlays without importing `pya` or mutating source layout data; the live KLayout batch lane passes with `KLAYOUT_EXE=C:\Users\edmun\AppData\Roaming\KLayout\klayout_app.exe`.
- Point capture is not implemented as a workflow yet, but it is now an explicit unavailable path: armed Shift-click returns a handled result with a message and does not mutate session or overlay state.
- Ellipsometry point capture is wired for the process-aware site-then-point child step in pure tooling, KLayout-boundary tests, and the opt-in live KLayout batch probe; general point-capture workflows remain deferred.
- Process output regeneration is solver-backed for attached recipes, exporter-backed for JSON summary artifacts when paths are configured, and warning-only for missing recipe, unavailable solver, parse failure, solver failure, or artifact export failure paths.
- Recipe editor card/header actions now route through a pure dispatcher. It supports safe
  in-memory card selection, validation, and add-step templates, while save/open/attach remain
  structured unavailable command results until real recipe persistence workflows are wired.
- The modeless recipe editor window now exposes an action callback for header/card actions. Recipe
  edits dispatch through `RecipeEditorActionDispatcher` and refresh the existing window; Close is a
  modeless controller action that updates the shared `WindowRegistry`.
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
- Session editor dispatcher tests covering `Open Output Folder` path handoff and no-session-folder
  unavailable behavior.
- Rendering pipelines, drawing persistence, SVG output, and fake rasterizer export paths.
- UI command routing and KLayout boundary/import isolation.
- Hybrid process solver pure fixtures, although solver integration is not the current alpha priority.
- New child-measurement workflow tests covering active-parent line capture, pending measurement
  review actions, retake/discard transitions, full measurement metadata edits, annotation artifact
  generation/regeneration, save/reload restoration, and render failure paths.
- Point capture tests covering normal-navigation preservation and explicit unavailable results through the direct tool and KLayout gesture adapter.
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
- Opt-in KLayout batch smoke coverage for `KLayoutCaptureGestureAdapter` inside a real `pya` runtime, including saved measurement line, profilometry compound child-line capture, and ellipsometry compound child-point capture, gated by `MPP_RUN_KLAYOUT_TESTS=1`; current evidence is 8 passing live KLayout integration tests.
- Opt-in KLayout GUI automation covers real menu registration and main-window snapshot probes through `MPP_RUN_KLAYOUT_UI_TESTS=1`, `klayout_app.exe`, and GUI `-e -rm` execution; current evidence is 2 passing live KLayout UI automation tests.

## Tests Still Needed

- Broaden opt-in live KLayout smoke coverage beyond batch probes if a stable GUI automation lane becomes available.
- App-level discovery/configuration tests for installed external JSON mode folders.
- Recipe file open workflow tests once file-picking paths are wired behind commands.

## Safe Reuse Points

- Keep using `SessionDocumentBuilder`, `EditorActionDispatcher`, `CanvasInteractionEngine`, and `CanvasOverlayManager` as the main editor/canvas seams.
- Keep artifact status and repair visibility in `ArtifactRecord` and `WarningRecord`.
- Keep KLayout/Qt code behind infrastructure and UI adapters.

## Do Not Touch Yet

- Do not fork mode-specific editor dialogs for measurement review.
- Do not add KLayout shape mutation for overlays.
- Do not replace canonical session JSON or move canonical state into UI widgets.
- Do not integrate the process solver into alpha capture workflows until capture/editor persistence is steadier.
