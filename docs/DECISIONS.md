# Process Planner Decisions

Last updated: 2026-06-24

## Canonical Data

- Session JSON remains the canonical persistent document.
- Artifacts remain first-class records in the central registry.
- Owner records keep local `artifact_refs` only as convenience references to registry IDs.
- Legacy embedded image, drawing, and export records are migration inputs only. Runtime code, editor previews, diagnostics, CSV export, and render refresh use the central artifact registry.
- Integer-schema fields such as old `capture_type` are translated only during legacy session migration. Canonical v5 record constructors read canonical fields such as `type` and generated CSV artifacts use the same vocabulary.
- UI/editor state such as selected tabs or window geometry is not persisted as canonical session data.

## Editor And Canvas

- The unified editor uses `SessionDocument` and dispatches explicit `EditorAction` values.
- UI shells should not directly mutate session JSON, run solvers, generate reports, or write files.
- Deferred or unavailable actions should set `EditorAction.enabled = False` with a
  `disabled_reason`; UI shells render the reason and dispatch returns it as a structured
  unavailable result if the action is routed anyway.
- Session editor callbacks must rerender through the shell contract after dispatch, using the rebuilt `SessionDocument`; model updates without visible shell refresh are considered stale UI bugs.
- Canvas visuals are durable `CanvasObject` records and overlay commands; KLayout source layouts remain read-only.
- Selection sync flows through `SelectionCoordinator` and document canvas-object indexes.
- KLayout capture gestures are normalized at the infrastructure boundary and routed through the shared capture tools; overlay restoration goes through `CanvasOverlayManager`, never source-layout shape insertion.
- Point capture remains a deferred workflow, but armed Shift-click is an explicit handled-unavailable result so host navigation and future mode contracts are predictable.
- Unknown saved session modes load through the built-in `simple_capture` fallback, with the requested mode preserved under `extensions.mode_validation` and surfaced as a warning/audit event.
- UI command routing emits lightweight `CommandRouted` diagnostic events so Advanced Diagnostics can show recent command activity without coupling to concrete widgets.
- Modeless UI state is summarized by pure state-machine evaluators before widgets render. Diagnostics, editor headers, and setup/recipe shells should consume state snapshots instead of re-inferring state from widget flags.
- Render refresh failures upsert failed owner/role SVG artifacts with repair metadata, so retries update one canonical repair target instead of piling up warnings or hidden error state.
- Live KLayout line-capture coverage is an opt-in batch probe that drives `KLayoutCaptureGestureAdapter` inside `pya` against a real layout and asserts source shapes are unchanged.
- Profilometry child-line capture reuses the same KLayout line gesture adapter and `LineCaptureTool`; durable workflow state decides whether line release creates a measurement child or a profilometry compound feature.
- Ellipsometry child-point capture reuses the same KLayout gesture adapter and `PointCaptureTool`; durable workflow state decides whether a Shift-click creates a compound point feature or returns the generic point-capture unavailable result.
- KLayout executable discovery treats inaccessible candidate paths as unavailable so release/integration checks skip or fail cleanly instead of crashing on Windows permission errors.
- Built-in workflow modes are declared as pure `ModeDefinition` records in a `ModeRegistry`; mode definitions are typed policy blocks for capabilities, setup, capture, metadata, measurements, artifacts, process, editor, and reporting, while mouse handling and persistence stay in shared services.
- Built-in mode declarations live outside the registry contract. The registry owns validation and lookup; `mode_builtins` owns built-in data construction.
- External custom modes are loaded from JSON as data-only `ModeDefinition` records. Unknown JSON fields are preserved as inert extension data; the loader must not import or execute custom Python.
- Profilometry and ellipsometry use the shared compound capture service. They may supply declarative mode/request data, but they do not get separate mouse handlers, persistence paths, or editor windows.
- Pending composite review uses generic `EditorAction` values and shared workflow services for save, retake inner feature, retake site box, discard, and exit. The pending review presenter renders adapter-provided view models instead of hard-coded action lists.
- Compound review workflows use typed command contracts for save, retake parent, retake inner feature, discard, and exit. Editor dispatch constructs commands and workflow services own state mutation.
- Composite editor selection indexes both parent and child canvas objects for pending and saved composite captures. Saved composite geometry features are normalized as generic `feature` editor items, not new persisted records, so selecting a child line/point can highlight only the child overlay.
- Saved composite capture actions are supplied by a dedicated capture action policy that reads canonical capture type and feature data. Profilometry and ellipsometry labels differ, but the commands remain generic editor actions routed through shared workflow services.
- Process context is a session-level workflow service with command models. Editor actions route to attach, detach, validate, fingerprint refresh, and regeneration hooks; UI code does not mutate process JSON directly.
- Process warning repair affordances are derived from `WarningRecord` data by the editor adapter and dispatched as generic editor actions. Warning dismissal marks `WarningRecord.status = "ignored"` and keeps canonical warning history intact.
- Dashboard process-context status is warning-aware: structured open warning codes drive missing, mismatch, and unavailable statuses so the Qt shell can render generic metadata fields without embedding process validation logic.
- Opening a recipe from the editor is a typed action result that hands a validated path to the UI shell; workflow dispatch does not launch external applications directly.
- Canonical session JSON exposes process context under `process_context.active` because process-aware captures reference `process_context.active`; flat process-context payloads are accepted only through integer-schema migration.
- Process-context validation is collected by a dedicated workflow helper. Validation produces structured warnings for missing recipes, missing solver backends, missing render profiles, stale process outputs/artifacts, and process-aware captures that are not linked to `process_context.active`.
- Process-aware capture inspector fields are built from canonical capture extensions, session process context, and `ProcessOutputRecord` statuses through shared metadata-field builders; the Qt/editor shell does not inspect profilometry or ellipsometry internals.
- Process-aware capture detection is structural: workflow code looks for extension blocks with solver requests or `process_context.active` references, not specific extension names such as `profilometry` or `ellipsometry`. Custom modes can therefore own process outputs under their own typed extension namespace.
- Pending composite review fields consume `ModeDefinition.metadata.field_ids()` through a shared metadata-field adapter. Built-in modes declare profilometry/ellipsometry field IDs, and the editor renders them without mode-specific review widgets.
- `ModeWorkflowPlanner` maps declarative mode policies into shared workflow requests. Built-in profilometry and ellipsometry compound requests are now generated from mode capture/process policy rather than hand-coded workflow constants.
- Capture release routing uses mode policy resolution for compound child steps. Line and point capture tools no longer branch on built-in profilometry or ellipsometry mode IDs; they ask the active mode policy whether the child step is a line or point.
- Compound child overlay object type is mode-declared through capture policy. Built-ins still use `profilometry_line` and `ellipsometry_point`, while custom line modes can persist overlays such as `fib_cut` without reusing profilometry object types.
- Compound child display labels are mode-declared and persisted on feature payloads. Editor actions use those labels, so custom line-based modes can show labels such as `FIB Cut` without getting generic profilometry/line wording.
- Saved process-aware capture extensions use mode-specific feature keys (`line_feature_id` or `point_feature_id`) and include empty solver-output containers (`outputs` for profilometry and `point_stack` for ellipsometry) so future solver data has a stable home.
- Built-in process-aware modes declare the full placeholder artifact role set, including `full_stack_compressed_image` for profilometry and `film_thickness_summary` for ellipsometry. Compound capture save creates central registry records for those placeholders.
- Process-output regeneration may call `HybridCrossSectionSolver` from workflow code when a recipe is attached. The workflow stores a compact solver summary in `ProcessOutputRecord`; configured app/editor services use `ProcessOutputStore` to write concrete JSON artifacts and mark process-output artifact records `present`.
- Process-output editor items read preview artifacts from `ProcessOutputRecord.artifact_refs`, filtered to registry artifacts of type `process_output`, and route regeneration through the output's canonical `metadata.capture_id`.
- Recipe editor card/header actions route through `RecipeEditorActionDispatcher`. The dispatcher
  normalizes view-model action IDs to typed `CommandId` values, applies only safe in-memory edits
  such as card selection or adding partial step templates, and leaves file save/open operations
  explicitly unavailable until a real workflow handler is wired.
- Recipe material card actions use explicit command IDs for add, duplicate, delete, visibility
  toggle, and usage lookup. These actions operate on in-memory `ProcessRecipe` values and return
  structured modeless results; deleting referenced materials stays blocked until a
  destructive-confirmation workflow exists.
- Material detail edits are command-routed with payload-bearing `EditMaterial` action IDs. Core
  fields stay on `Material`, while material category/notes remain in recipe metadata extension
  blocks so the current recipe schema does not grow ad hoc wrapper fields.
- Inline recipe validation messages expose selection action IDs rather than launching dialogs. The
  shell can dispatch the existing `SelectRecipeCard` command to reveal the related card detail.
- Process-step detail edits are command-routed with payload-bearing `EditProcessStep` action IDs.
  Editable fields are applied to typed `ProcessStep` data or its parameter map, keeping generated
  summaries and solver-facing recipe data in sync without widget-side mutation.
- Closing a dirty recipe editor is not a silent close. The controller returns a structured blocked
  result for `CloseRecipeEditor` and only closes dirty recipes through the explicit
  `CloseRecipeEditor:discard` confirmation path.
- Recipe JSON persistence lives behind `ProcessRecipeJsonStore`. The recipe editor controller may
  call it for `SaveRecipe` when a recipe path is known, or `SaveRecipeAs:<path>` when a shell
  supplies a new destination, but widgets and pure dispatchers do not write recipe files directly.
- Recipe switching is also controller-owned. `NewRecipe` and `OpenRecipe:<path>` block when the
  current recipe is dirty, and only `NewRecipe:discard` / `OpenRecipe:discard:<path>` replace the
  active recipe after an explicit confirmation.
- Attaching a recipe to the active session is a typed app-level bridge. The recipe editor supplies a
  saved recipe path, the process-context workflow updates `SessionRecord.process_context`, and the
  session editor is rebuilt from the updated canonical session. Widgets never mutate session JSON
  or process-context fields directly.

## Child Measurement Slice

- `ADD_MEASUREMENT` starts by marking the selected saved capture canvas object as the active parent and setting durable workflow state to `measurement_line`.
- A child line is stored as a nested `MeasurementRecord` under the owning `CaptureRecord`.
- Pending child measurements use `measurement.metadata["workflow_state"] == "pending"` instead of a separate top-level pending-measurement store.
- Saving editor edits promotes pending measurements to `workflow_state == "saved"` and updates the measurement canvas object to `CanvasWorkflowState.SAVED`.
- Saved measurements refresh measurement-owned `measurement_annotation` drawing artifacts through the existing render bridge and drawing store.
- If annotation generation cannot run, saved measurements may still carry a pending artifact/warning repair task instead of blocking canonical session save.
- Measurement annotation regeneration uses the generic `REGENERATE_ARTIFACT` editor action for measurement items rather than adding a mode-specific command.
- Pending measurements expose `SAVE_MEASUREMENT`, `RETAKE_MEASUREMENT_LINE`,
  `DISCARD_MEASUREMENT`, and parent-return actions through the generic editor adapter. Retake and
  discard are pure workflow transitions and do not require a separate measurement review dialog.
- The allowed post-measurement prompt is carried as `EditorActionResult.post_action_prompt`
  after `SAVE_EDITS` promotes a pending measurement. Prompt choices are applied through
  `MeasurementCompletionChoice`; Qt should render those choices rather than inventing dialog logic.

## Rendering And Solver Boundaries

- Rendering remains a pure scene/SVG pipeline with rasterization injected at the Qt/KLayout boundary.
- The process solver remains pure Python and does not import KLayout, Qt, the editor, or PowerPoint.
- Solver-backed summaries are allowed in the alpha workflow, and exporter-backed process artifact files stay behind the persistence `ProcessOutputStore` boundary rather than UI or solver code.
- Canonical artifact ID generation is separate from legacy artifact conversion. Legacy image/drawing/export records are migration inputs only.
- Current workflow services must create and attach owner `artifact_refs` explicitly when they create artifacts; `SessionRecord` construction does not hydrate old wrapper fields or infer owner refs from the registry.

## Refactoring Policy

- Prefer small helper extraction over broad rewrites.
- Keep legacy conversion code at file/input boundaries only; do not hydrate old artifact wrappers or old field names back into current session records.
- Add characterization tests before changing workflow behavior.
