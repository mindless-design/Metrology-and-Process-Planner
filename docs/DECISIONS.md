# Process Planner Decisions

Last updated: 2026-06-25

## Canonical Data

- Session JSON remains the canonical persistent document.
- The current canonical session JSON schema remains `5.0.0`. The `1.0.0` shape in the urgent
  lifecycle request is treated as an illustrative minimum, not a downgrade target.
- The editable session document is `session.json`; no database or CSV/image-only persistence layer
  is allowed to become the source of truth for captures, artifacts, warnings, workflow resume
  state, or process/report context.
- `SessionDocument` wraps the typed `SessionRecord`, carries the loaded path, dirty state, revision,
  and raw payload, and is the editor boundary. New workflow features should not pass loose session
  dicts through UI/app code.
- There is one active editable Process Planner session by default. `ActiveSessionContext` is the
  app-layer record for active session id, path, document, layout binding, dirty state, revision,
  workflow state, and selected item.
- Unknown top-level JSON fields are preserved where practical during document save so future or
  extension payloads are not discarded by routine editor edits.
- Artifacts remain first-class records in the central registry.
- Owner records keep local `artifact_refs` only as convenience references to registry IDs.
- Visual artifact polish keeps the existing `site_image` role as the raw capture image and registers
  derived capture-owned artifacts for labeled site images, site-specific overviews, and polished
  annotation images. Shared `LabelSpec` / `LabelStylePolicy` models provide label text and styling
  across site, overview, annotation, and cross-section render paths; artifact `extensions` carry
  style/profile ids so this does not require a session JSON schema break.
- Legacy embedded image, drawing, and export records are migration inputs only. Runtime code, editor previews, diagnostics, CSV export, and render refresh use the central artifact registry.
- Artifact lifecycle v1 extends central `ArtifactRecord` data instead of scattering output
  filenames through owner records. Artifact scans are pure Python and do not require live KLayout;
  live layout, recipe, solver, and parent-image requirements are expressed as repair metadata and
  structured warnings. UI and diagnostics surfaces call `ArtifactRepairService`/scanner results
  through command/service routing instead of regenerating files directly.
- Integer-schema fields such as old `capture_type` are translated only during legacy session migration. Canonical v5 record constructors read canonical fields such as `type` and generated CSV artifacts use the same vocabulary.
- Capture geometry remains backward-compatible with raw `bounds`, `start`, `end`, and `point`
  fields, but box captures also serialize computed `geometry.primary` metadata with bounds,
  center, width, height, units, and coordinate mode. Compound feature payloads remain under
  `capture.geometry.features` and are normalized in memory/JSON with line midpoint/length or point
  coordinate plus a parent geometry reference. CSV, editor metadata, and reports should consume
  these canonical geometry records rather than recomputing mode-specific export payloads.
- Line, point, and measurement annotation artifacts use the shared drawing scene/export pipeline.
  Mode-declared roles such as `line_annotation` and `point_annotation` are render targets for the
  same shared renderer, not separate mode-specific renderers. Annotation failure remains
  non-blocking and is represented by warnings plus placeholder or failed artifact records.
- Process-aware visual outputs resolve render profiles through one shared role/type mapping:
  profilometry uses `profilometry_surface_profile`, ellipsometry/point-stack outputs use
  `point_stack_schematic`, FIB uses `fib_full_stack_compressed`, and process-flow frames use
  `process_flow_frame`. Missing or invalid profile selections fall back to
  `physical_cross_section` with `RENDER_PROFILE_MISSING` rather than crashing generation.
- Length parsing and conversion use the shared `domains.units` contract. Session display-unit
  preferences are additive session extensions that control UI/report/export formatting without
  changing canonical recipe, solver, capture, or artifact values. Legacy unitless recipe thickness
  values continue to load as micrometers.
- Process material identity, aliases, colors, and unknown-material behavior live in the shared
  process material catalog. Renderers, recipe import, reports, and tests should resolve aliases
  through that catalog instead of maintaining local material/color palettes.
- Cross-section scenes keep solver geometry separate from presentation. Scene axes, ticks, scale
  bars, measurement labels, and report captions format from the solver result's source units
  through display-unit preferences; `coordinate_frame.source_units` records the source unit while
  the legacy `coordinate_frame.canonical_units` key remains load-compatible.
- Process-aware renderers, site images, annotation images, and overview diagrams default to the
  shared `engineering_dark` theme. Labels, leaders, legends, placeholders, and warning badges use
  theme-owned colors and sizes so foreground marks stay visible on the selected background without
  changing canonical solver geometry.
- Render-stage simplification is metadata-only and must not mutate canonical solver geometry.
  Profiles may hide buried clutter, compress thick visual regions, preserve thin critical films,
  or simplify sub-pixel slivers for readability, but scenes/artifacts must record
  `RENDER_SIMPLIFICATION_APPLIED` and simplification notes when those choices affect the visual
  presentation.
- `LayoutToImageTransform` is the shared layout/image coordinate mapper for annotation placement.
  It supports y-axis orientation, origin-relative coordinates, and padding/crop margins so capture
  adapters can document coordinate conventions without changing persisted geometry semantics.
- UI/editor state such as selected tabs or window geometry is not persisted as canonical session data.
- Recent sessions are a UI convenience registry of `session.json` paths, not canonical session data.
- Missing source layouts must not block opening a session. They become warnings and can be repaired
  later by binding a current layout explicitly.
- Save is always a document write: apply pending editor metadata, validate, write temp JSON, back up
  the existing `session.json`, atomically replace, clear dirty state, and update the modified
  timestamp.
- Dirty close requires an explicit save/discard/cancel choice from the UI/controller caller.

## Editor And Canvas

- Session document menu inputs are adapter-owned. `SessionPathAdapter` supplies folder/file/recent
  and save-as destinations; `SessionLayoutAdapter` supplies current KLayout layout metadata. App
  command handlers translate those inputs into controller lifecycle calls, while workflows remain
  free of Qt dialogs and live KLayout imports.
- Binding a current layout is a document command, not a widget mutation. The command updates
  `SourceLayoutContext`, saves through the existing `SessionStore`, creates structured
  `SOURCE_LAYOUT_MISMATCH` warnings for incompatible rebinding, and restores durable overlays via
  `CanvasOverlayManager` when a host overlay backend is supplied.
- The production KLayout session editor shell is injected through the same `SessionEditorShell`
  widget-factory contract used by tests. KLayout startup may supply a Qt-backed factory, but the
  rendered regions still come from `SessionDocument` presenters and callbacks still route through
  controller/command boundaries.
- Modeless windows are owned by `WindowRegistry` through named product-surface methods:
  `get_or_create_session_editor`, `get_or_create_setup_guide`,
  `get_or_create_recipe_editor`, and `get_or_create_diagnostics_panel`. Controllers pass
  view-model render callbacks into that registry boundary instead of hand-owning duplicate
  top-level windows.
- The unified editor uses `SessionDocument` and dispatches explicit `EditorAction` values.
- UI shells should not directly mutate session JSON, run solvers, generate reports, or write files.
- Deferred or unavailable actions should set `EditorAction.enabled = False` with a
  `disabled_reason`; UI shells render the reason and dispatch returns it as a structured
  unavailable result if the action is routed anyway.
- Session editor callbacks must rerender through the shell contract after dispatch, using the rebuilt `SessionDocument`; model updates without visible shell refresh are considered stale UI bugs.
- Session editor navigator search and warning filters are transient controller/shell state. They
  filter rendered navigator rows while preserving non-empty groups and must not be persisted into
  canonical session JSON.
- Session editor header actions split by responsibility: document mutations remain in
  `EditorActionDispatcher`, but header entrypoints route through app commands where the command
  catalog owns the user intent. `SaveSessionEdits` delegates to the active editor dispatcher and
  returns document/selection metadata, while window/lifecycle intents such as reopen setup and
  close route through the app `CommandRouter` so menus and editor buttons share diagnostics and
  blocked-result behavior.
- Selected-item editor workflow commands are active-session commands, not widget-private logic.
  Pending capture, composite capture, measurement, artifact regeneration, process-output
  regeneration, and discard-unsaved-edits commands resolve the current `SessionDocument` selection
  and delegate to the existing editor dispatcher. The command layer owns routing/status metadata;
  the workflow layer still owns state transitions.
- Payload-bearing editor commands preserve the originating `EditorAction` while app command
  routing is active. This lets process actions such as attach-recipe carry a selected path through
  `CommandRouter` without adding modal file-picker logic to workflows, while direct payload-less
  command invocations remain structured unavailable results.
- Post-measurement continuation choices are workflow commands. `TakeAnotherMeasurement` applies the
  existing measurement-completion workflow to the active editor document and refreshes selection;
  prompt widgets should dispatch that command instead of arming capture tools directly.
- Output-folder opening is a shell handoff, not workflow-side process launching. The editor
  dispatcher returns the resolved session folder via `EditorActionResult.output_path`; UI adapters
  decide how to reveal it.
- Export/path handoffs should still be commands. `ExportCSV` and `OpenOutputFolder` route through
  `CommandRouter` and preserve the dispatcher output path on `CommandRouteResult.output_path`,
  keeping diagnostics and shell handoff behavior on the same path.
- Canvas visuals are durable `CanvasObject` records and overlay commands; KLayout source layouts remain read-only.
- Selection sync flows through `SelectionCoordinator` and document canvas-object indexes.
- KLayout capture gestures are normalized at the infrastructure boundary and routed through the shared capture tools; overlay restoration goes through `CanvasOverlayManager`, never source-layout shape insertion.
- Point capture remains a deferred workflow, but armed Shift-click is an explicit handled-unavailable result so host navigation and future mode contracts are predictable.
- Unknown saved session modes load through the built-in `simple_capture` fallback, with the requested mode preserved under `extensions.mode_validation` and surfaced as a warning/audit event.
- UI command routing emits lightweight `CommandRouted` diagnostic events so Advanced Diagnostics can show recent command activity without coupling to concrete widgets.
- Advanced Diagnostics shell actions are controller-provided view models. The shell renders
  `EditorActionViewModel` rows for diagnostics/export/validation handoffs and does not invent
  action labels or availability rules locally.
- Advanced Diagnostics action dispatch is owned by an app-layer dispatcher. UI backends call the
  controller callback with an action ID and receive a structured result; the dispatcher emits
  route/failure diagnostics and returns unavailable/error results instead of letting widget
  callbacks swallow exceptions.
- Modeless UI state is summarized by pure state-machine evaluators before widgets render. Diagnostics, editor headers, and setup/recipe shells should consume state snapshots instead of re-inferring state from widget flags.
- Setup guide cards must render from action view models, not command-name guesses. Primary,
  secondary, and footer actions carry labels and disabled reasons from the setup state/policy
  layer so unavailable setup choices can be shown inline.
- Setup guide cards must also render requirement and artifact badges from presenter view models.
  Widgets should not inspect `SetupItemRecord.artifact_refs` or artifact registry state directly;
  the presenter supplies a compact artifact availability badge from canonical session data.
- Recipe editor cards own their displayed status/action view models. Process-step card widgets
  should render the supplied status label and `EditorActionViewModel` rows instead of rebuilding
  duplicate/move/enable/disable/preview-through-step rules locally.
- Render refresh failures upsert failed owner/role SVG artifacts with repair metadata, so retries update one canonical repair target instead of piling up warnings or hidden error state.
- Live KLayout line-capture coverage is an opt-in batch probe that drives `KLayoutCaptureGestureAdapter` inside `pya` against a real layout and asserts source shapes are unchanged.
- Profilometry child-line capture reuses the same KLayout line gesture adapter and `LineCaptureTool`; durable workflow state decides whether line release creates a measurement child, a profilometry compound feature, or a standalone pending line capture.
- Standalone line capture is a first-class pending capture workflow. When no compound line request
  or active parent measurement is present, line release commits `CaptureGeometry.line(...)` into a
  pending `CanvasObject` and `PendingCapture`; pending review promotes it through the same save/discard
  path as box captures.
- Ellipsometry child-point capture reuses the same KLayout gesture adapter and `PointCaptureTool`; durable workflow state decides whether a Shift-click creates a compound point feature or a standalone pending point capture.
- Standalone point capture is a first-class pending capture workflow. When no compound point request
  is active, `PointCaptureTool` commits Shift-click geometry into a pending `CanvasObject` and
  `PendingCapture` with `CaptureGeometry.point_capture(...)`; pending review then promotes it through
  the same save/discard path as box captures. The workflow does not invent an image crop path when a
  point click has no live image artifact, so saved point captures use the existing placeholder/warning
  path until a live point-image generator supplies one.
- KLayout standalone point and line capture coverage belongs in opt-in batch `pya` probes that drive
  `KLayoutCaptureGestureAdapter`, assert pending geometry and overlay commands, and verify source
  layout shape counts are unchanged.
- KLayout executable discovery treats inaccessible candidate paths as unavailable so release/integration checks skip or fail cleanly instead of crashing on Windows permission errors.
- Built-in workflow modes are declared as pure `ModeDefinition` records in a `ModeRegistry`; mode definitions are typed policy blocks for capabilities, setup, capture, metadata, measurements, artifacts, process, editor, and reporting, while mouse handling and persistence stay in shared services.
- Built-in mode declarations live outside the registry contract. The registry owns validation and lookup; `mode_builtins` owns built-in data construction.
- External custom modes are loaded from JSON as data-only `ModeDefinition` records. Unknown JSON fields are preserved as inert extension data; the loader must not import or execute custom Python.
- Profilometry and ellipsometry use the shared compound capture service. They may supply declarative mode/request data, but they do not get separate mouse handlers, persistence paths, or editor windows.
- Pending composite review uses generic `EditorAction` values and shared workflow services for save, retake inner feature, retake site box, discard, and exit. The pending review presenter renders adapter-provided view models instead of hard-coded action lists.
- Compound review workflows use typed command contracts for save, retake parent, retake inner feature, discard, and exit. Editor dispatch constructs commands and workflow services own state mutation.
- Composite editor selection indexes both parent and child canvas objects for pending and saved composite captures. Saved composite geometry features are normalized as generic `feature` editor items, not new persisted records, so selecting a child line/point can highlight only the child overlay.
- Saved composite capture actions are supplied by a dedicated capture action policy that reads canonical capture type and feature data. Profilometry and ellipsometry labels differ, but the commands remain generic editor actions routed through shared workflow services.
- Saved-capture replacement actions must be explicit workflow results. Generic recipe-free saved
  box captures use the shared replacement workflow: `Replace Capture` arms a durable replacement
  box capture, the next shared box gesture creates a pending replacement, and saving it reuses the
  original capture ID, sequence, metadata, and artifact ownership while superseding the old canvas
  object. Inner-feature replacement remains a structured unavailable result until a shared
  feature-replacement workflow is intentionally scoped.
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
- Recipe editor header state is a view model, not shell inference. `RecipeHeaderViewModel` carries
  path, dirty state, validation status, warning count, and attach readiness, while header actions
  carry disabled reasons for unavailable save/validate/preview/attach choices.
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
- Recipe preview commands may update in-memory preview scope before renderer/solver preview is
  connected. They return structured warning results and never run the solver from the widget layer.
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
- Setup-guide skip and validation actions are controller/service-owned commands. Skipping applies
  only to explicit optional `SetupItemRecord` stages in canonical setup state, while recipe-context
  validation delegates to the process-context workflow and stores warnings on the session for the
  editor/setup guide to render modelessly.
- Generic capture arming lives in an app-level `CaptureCommandService`, not in widgets or
  mode-specific handlers. The service owns only ephemeral interaction context plus durable
  workflow arming state, delegates gesture mechanics to `CanvasInteractionEngine`, and refreshes
  modeless editor/setup surfaces through session-document rebuilds.
- End-session lifecycle behavior is conservative and modeless. `EndActiveSession` closes safe
  session surfaces and clears capture arming only when there are no pending captures or dirty
  editor edits; otherwise it raises a typed blocked command condition so the router can show inline
  guidance and diagnostics can record a warning rather than a silent no-op.
- Command handlers may return `CommandRouteResult` when they have richer workflow context. The
  router preserves those statuses and emits warning/error diagnostics for returned unavailable,
  blocked, warning, or error outcomes even when no exception escaped the workflow boundary.
- Non-process-aware modes are recipe-free by default. Simple labeled capture, fast batch capture,
  CAD review, optical metrology, CDSEM measurement, and grid measurement declare
  `recipe_policy = forbidden`, `solver_operation = none`, and `supports_process_solver = false`;
  editor adapters must hide recipe/process/solver actions and process-output groups for these
  modes even if stale process records exist in a session. Optical and CDSEM setup remain modeless
  setup-guide stages routed through shared setup commands, not new mode-specific dialogs or mouse
  handlers.
- The session editor header uses the same mode-definition process-awareness rule as the editor
  adapter. Recipe/process context header fields and recipe actions are hidden for non-process modes
  instead of being inferred from incidental stale process-context fields.
- Grid measurement planning is a recipe-free workflow. Grid datasets store anchor capture refs,
  generated site coordinates, and a `grid_overview` artifact placeholder through the central
  artifact registry; invalid grid geometry becomes structured warnings instead of a solver or recipe
  dependency.
- Grid overview placeholders render as placeholder previews in the unified editor and expose
  artifact-specific `Regenerate Grid Overview` repair actions. They stay visible and repairable
  without recipe or solver context.

## Child Measurement Slice

- `ADD_MEASUREMENT` starts by marking the selected saved capture canvas object as the active parent and setting durable workflow state to `measurement_line`.
- A child line is stored as a nested `MeasurementRecord` under the owning `CaptureRecord`.
- Pending child measurements use `measurement.metadata["workflow_state"] == "pending"` instead of a separate top-level pending-measurement store.
- Saving editor edits promotes pending measurements to `workflow_state == "saved"` and updates the measurement canvas object to `CanvasWorkflowState.SAVED`.
- Saved measurements refresh measurement-owned `measurement_annotation` drawing artifacts through the existing render bridge and drawing store.
- If annotation generation cannot run, saved measurements may still carry a pending artifact/warning repair task instead of blocking canonical session save.
- Measurement annotation regeneration uses the generic `REGENERATE_ARTIFACT` editor action for measurement items rather than adding a mode-specific command.
- Overview labeling is a shared rendering backbone under `rendering.overview`. Session user labels are
  durable `UserLabelRecord` payloads stored non-breakingly in `session.extensions["overview"]`;
  captures, measurements, process features, and user labels all become `LabelTarget` records before
  content, placement, leader routing, scene creation, and artifact rendering. The unified editor
  generates session-level overview SVG artifacts through the central artifact registry, and reports
  consume those artifacts by role instead of depending on live editor state.
- Overview artifacts carry a compact `report_summary` extension in addition to full scene JSON. The
  reporting model preserves artifact extensions, and overview report sections render digest lines
  plus figure notes from that summary so PowerPoint/PDF/image exporters do not need to understand
  the full layout scene schema.
- Pending measurements expose `SAVE_MEASUREMENT`, `RETAKE_MEASUREMENT_LINE`,
  `DISCARD_MEASUREMENT`, and parent-return actions through the generic editor adapter. Retake and
  discard are pure workflow transitions and do not require a separate measurement review dialog.
- The allowed post-measurement prompt is carried as `EditorActionResult.post_action_prompt`
  after `SAVE_EDITS` promotes a pending measurement. Prompt choices are applied through
  `MeasurementCompletionChoice`; Qt should render those choices rather than inventing dialog logic.
- App-level session editor command results preserve `post_action_prompt` from editor workflow
  results. Toolbar/command-router saves and direct editor dispatch therefore expose the same
  recipe-free follow-up choices after a measurement is promoted.

## Rendering And Solver Boundaries

- Rendering remains a pure scene/SVG pipeline with rasterization injected at the Qt/KLayout boundary.
- The process solver remains pure Python and does not import KLayout, Qt, the editor, or PowerPoint.
- Solver output contracts live in the process domain. `SolverResult`, `ProcessFrame`, and
  `RenderProjection` carry backend IDs, input hashes, units, material metadata, physical bounds,
  changed-region metadata, diagnostics, and approximation notes so renderers and reports do not
  inspect private solver helpers or recipe internals.
- `StackInvariantChecker` and `validate_render_projection()` are public process-domain validation
  hooks. Strict solver mode runs these checks after each step/final projection, while normal mode
  preserves user-facing diagnostics without making the renderer guess which failure mode occurred.
- Etch target exhaustion and non-target blockers are solver diagnostics, not renderer or UI special
  cases. The sampled geometry result remains usable, while `ETCH_TARGET_EXHAUSTED` and
  `ETCH_BLOCKED_BY_NON_TARGET` explain why requested removal did not fully occur.
- The default solver frame behavior remains backward-compatible with existing process-flow tests:
  `frame_every_step=True` emits every step frame, and each frame records `changed_from_previous`.
  Renderers that need canonical changed-only frame sequences should filter on that field; debug
  workflows can preserve unchanged frames explicitly.
- Cross-section rendering uses a staged pipeline:
  `SolverResult`/stack geometry -> `RenderIntent`/`RenderProfile` -> filtered geometry ->
  visual projection -> `CrossSectionSceneModel` -> replaceable renderer -> artifact record.
- Physical truth stays in solver geometry. Visual communication choices such as surface-only
  filtering, full-stack compression, thin-layer exaggeration, conformal emphasis, labels, leaders,
  and callouts are recorded in render profile, transform, scene, compression, warning, and artifact
  metadata.
- UI widgets must request or preview rendered artifacts through render profiles and artifact records;
  they must not construct cross-section geometry directly.
- Renderers must not mutate solver geometry or depend on KLayout UI state. The default backend adapts
  `CrossSectionSceneModel` into the existing editable SVG drawing pipeline and can be replaced by a
  later PDF, PowerPoint, or KLayout-scene backend.
- Solver-backed summaries are allowed in the alpha workflow, and exporter-backed process artifact files stay behind the persistence `ProcessOutputStore` boundary rather than UI or solver code.
- Canonical artifact ID generation is separate from legacy artifact conversion. Legacy image/drawing/export records are migration inputs only.
- Current workflow services must create and attach owner `artifact_refs` explicitly when they create artifacts; `SessionRecord` construction does not hydrate old wrapper fields or infer owner refs from the registry.

## Refactoring Policy

- Prefer small helper extraction over broad rewrites.
- Keep legacy conversion code at file/input boundaries only; do not hydrate old artifact wrappers or old field names back into current session records.
- Add characterization tests before changing workflow behavior.

## Reporting Workbench Boundary

- Report generation is split between a pure reporting engine and a modeless KLayout workbench. The
  engine consumes `SessionDocument`, artifact records, mode reporting policy, report templates, and
  `ReportRequest`; it can validate, build, and export reports without importing Qt, KLayout, or live
  editor state.
- The Reporting Workbench is an app/UI surface for preview, template selection, readiness, repair
  actions, and export commands. It opens from the Session Editor and the Process Planner menu through
  `OPEN_REPORTING_WORKBENCH`, but it rebuilds view models from the active `SessionDocument` rather
  than selected widgets, canvas overlays, or live layout view state.
- Unified editor and review surfaces label the report entrypoint as `Build Report`. The underlying
  compatibility action id remains `build_powerpoint`, but recipe-free modes should not foreground
  PowerPoint-specific language in normal capture and measurement workflows.
- Missing or stale report images are handled through placeholder policy and readiness findings. Live
  KLayout regeneration remains a convenience hook to be routed through an artifact repair service;
  report exporters must not call KLayout screenshot or layout-export APIs directly.
- Visible placeholder artifacts produce non-blocking report readiness warnings. Exports may proceed
  with placeholders, but the workbench and diagnostics can still surface the repair need.
- Generated decks, PDFs, CSV exports, image bundles, and manifests are report-owned artifacts. Report
  regeneration supersedes prior report-owned artifacts unless a future explicit overwrite workflow is
  added.
- Generated PowerPoint report artifacts carry `rebuild_report` repair metadata and route through the
  built-in artifact repair service. The repair handler reconstructs a `ReportRequest` from the saved
  `ReportRecord`, removes stale prior outputs from the build document so they cannot block their own
  repair, and then delegates to the headless reporting service.
- Workbench defaults are mode-aware but declarative: the app selects a built-in template from the
  active session mode/family, then lets mode reporting policy add sections without exporter changes.
- Successful exports refresh the active Session Editor document through an injected updater so report
  artifacts appear immediately, while the core exporter still returns a session value instead of
  mutating UI state.
- Report output QA favors structural assertions over pixel-perfect comparisons: PPTX tests validate
  native shapes, relationship targets, placeholder visibility, bounds, and non-overlap; PDF tests
  validate parseable outlines/text and nonblank rendered pages when the optional renderer is present.
- Report output themes are part of `ReportRequest` and report metadata. Built-in light/dark themes
  are exporter-neutral palettes consumed by PPTX and PDF backends, recorded in manifests, and exposed
  through the Workbench model so KLayout UI theme selection does not leak into headless generation.
- Report captions, section context, page/slide footers, and visual table alignment are derived at
  export time from `ReportDocument`; they do not add persisted session fields or mode-specific
  exporter branches. CSV keeps complete machine-readable values while PPTX/PDF may use compact
  display text for visual clarity.
# Synthetic Process Laboratory

- The synthetic GDS is generated with a small standard-library GDSII writer so
  fixture regeneration does not require a new dependency or a KLayout UI.
- Pure Python geometry extraction reads the deterministic sidecar manifest; the
  binary GDS remains available for optional KLayout smoke tests.
- Golden comparisons use compact JSON summaries rather than image-only tests.
- Recipe JSON avoids a schema-breaking change. Specialized future solver inputs
  that are not currently deserialized by `ProcessRecipe.from_dict()` are stored
  in metadata/parameters and documented as future schema work.
- Broken sessions live under `tests/fixtures/synthetic_sessions/broken/` and
  advertise expected diagnostic targets without poisoning canonical fixtures.

## Recipe-Free Capture Sequencing

- Generic repeated capture uses monotonic pending and capture IDs derived from existing saved capture
  sequences, not only currently pending records. This prevents simple and fast-batch workflows from
  reusing `images/pending-001.png` after the first pending capture is saved.
- Auto-generated fast-batch labels follow the same monotonic sequence as the saved capture ID:
  `Capture 001`, `Capture 002`, and so on. Deleted or superseded captures do not cause later captures
  to reuse labels or image artifact paths.
- CAD review captures default to `layout_issue` when no review category is supplied, matching the
  editor metadata default and keeping CSV/report categories stable.

## Recipe-Free Setup Stages

- Modes with declared setup stage lists render those stage lists as authoritative cards on every
  setup-guide open. Persisted setup items overlay status, warnings, and artifact badges onto the
  declared cards instead of replacing the whole guide.
- Optical and CDSEM setup cards keep stable stage IDs such as `optional_origin_point`,
  `optical_alignment`, `sem_alignment`, and `ready_for_capture` so reopen behavior and command
  routing remain mode-driven without adding mode-specific dialogs.
- Once all required setup stages are complete, a valid `is_capture_ready` flag selects the
  `ready_for_capture` card even if optional setup cards were left unfinished. Stale ready flags are
  still rejected whenever required optical/SEM alignment stages are incomplete.
- The completed `ready_for_capture` card keeps `Mark Setup Complete` visible but disabled with an
  explicit reason, so setup-ready recipe-free modes explain the state instead of presenting a silent
  disabled action.

## Recipe-Free CSV Artifacts

- Capture CSV export remains recipe-free and writes the canonical `captures.csv` file in the
  session folder. A successful export also upserts a session-owned `csv_export` artifact record so
  artifact scans, repair actions, diagnostics, and editor readiness can reason about the generated
  file.
- CSV freshness is tied to a lightweight `session_data` dependency signature. The signature excludes
  existing CSV export artifacts to avoid self-staleness, but includes captures, measurements through
  capture serialization, grid datasets, non-CSV artifact status, warnings, mode, coordinates, and
  source-layout context.
- Recipe-free dashboards derive CSV readiness from the visible session-owned CSV artifact. Sessions
  with no generated CSV show `not exported`, present CSV artifacts show `ready`, stale CSV artifacts
  show `stale`, and missing or failed CSV artifacts show that export needs attention without
  requiring recipe or solver context.

## Recipe-Free Artifact Repair State

- Modeless artifact repair state is mode-aware. Non-process-aware sessions expose generic artifact
  repair actions such as `RegenerateArtifact` and do not advertise `RegenerateProcessOutput`.
- Placeholder artifacts with explicit repair metadata count as open repair tasks so grid overviews,
  measurement annotations, and other non-blocking placeholders remain visible and repairable without
  requiring recipe or solver context.

## CDSEM Mode Identifier Compatibility

- `cdsem_measurement` is a first-class built-in recipe-free mode id. The older `cdsem_capture` id
  and the `cdsem_planning` compatibility id remain registered so existing saved/planning sessions
  continue to load without migration or duplicate operator-visible modes.
- All CDSEM ids share the same non-process setup, measurement, metadata, artifact, report-template,
  and default capture policies, including the required optical and SEM alignment stages.
- CDSEM capture metadata includes a read-only label guidance row in the generic editor. This keeps
  label-length guidance modeless and avoids adding CDSEM-specific review dialogs.

## Recipe-Free Measurement Metadata Editing

- Measurement `target`, `lower_spec_limit`, and `upper_spec_limit` are optional metadata in
  recipe-free workflows. Blank editor values clear those fields instead of preserving stale numeric
  values.
- Required rendering metadata such as line weight remains validated as positive numeric data and is
  not cleared by blank input.

## Recipe-Free Setup Command Routing

- `ValidateRecipeContext` remains registered globally for command catalog stability, but the setup
  command handler blocks it for non-process-aware modes. Direct command routing must not create
  recipe warnings or mutate process context in simple, batch, CAD review, optical, CDSEM, or grid
  sessions.
- Process-aware setup modes still use the same command path for recipe validation and warning
  persistence.
- Modeless setup commands update the active Setup Guide session and refresh the active unified
  editor document when the setup guide was opened from the editor. Coordinate choices, setup capture
  arming, skipped optional stages, and ready-state changes must not remain trapped in a setup-only
  controller state when the user returns to the editor.
- Setup-guide production rendering uses host-ready card models rather than letting Qt infer
  workflow semantics. `SetupStageCardModel` carries status tone, requirement, artifact, warning,
  action, disabled, and active-stage metadata, and KLayout registration injects
  `KLayoutSetupGuideSurfaceFactory` through the same `ModelessSurfaceShell` boundary used by pure
  tests.
- Optional setup skipping is active-card driven. `SkipOptionalSetupStage` advances through optional
  origin point/reference cards one at a time, leaves already skipped cards alone, and blocks direct
  command routing when the active card is required, such as optical or SEM alignment.

## Recipe-Free Process Action Guard

- Editor process-context actions are guarded at dispatch time as well as hidden by adapters. Directly
  constructed attach, detach, validate, fingerprint, or regenerate-process-output actions return
  unavailable for non-process-aware sessions.
- Stale process context or process-output records in a recipe-free session are treated as hidden
  legacy data; they do not make the active mode process-aware.
- The modeless recipe editor uses the same mode boundary when attaching its current recipe to the
  active unified-editor session. Recipe-free sessions reject that command modelessly and remain
  unmodified.
- Report readiness validates the effective template sections rather than raw requested section ids.
  In recipe-free sessions, stray process-context section selections are ignored instead of producing
  recipe-required errors; process-aware templates still require attached process context.
- UI state-machine diagnostics treat recipe context as `hidden` for recipe-free modes, even if a
  legacy process context or process warning exists on the saved session. Direct UI-state evaluation
  must not expose attach, detach, or validate recipe actions outside process-aware modes.
- Artifact repair requests also hide process-only repair artifacts in recipe-free modes. Stale
  legacy process-output artifacts, recipe-required repairs, and solver-required repairs must not
  create repair queue entries, recipe-required warnings, or process-output actions for simple, batch,
  CAD review, optical, CDSEM, or grid sessions.
- Generic measurement metadata accepts both record-native keys and mode-facing aliases. `edge_convention`,
  `color`, and `line_weight_px` map onto `edge_detection_convention`, `annotation_color`, and
  `line_weight` so CDSEM and other recipe-free mode schemas can use concise field names without
  forking the measurement editor.
- Post-measurement completion prompts are one-shot and tied to newly promoted measurements through
  `completion_prompt_pending` metadata. Completion choices clear the marker so old saved
  measurements cannot re-trigger prompts or re-arm the wrong parent capture.
- Setup readiness for declared setup modes is derived from required stage completion as well as the
  persisted `is_capture_ready` flag. Optical and CDSEM sessions that reopen with stale ready state
  but missing required alignment cards render the first unresolved setup card and keep Ready for
  Capture blocked.
- Setup guide cards use the same recipe-free visibility rules for persisted warning IDs and artifact
  badges. Hidden process-context warnings and hidden process-output artifacts do not make optical,
  CDSEM, or other recipe-free setup cards look blocked, warning-heavy, or artifact-broken.
- Setup guide stage construction threads the active `ModeRegistry` into persisted setup-item warning
  and artifact badge filtering. Loaded external recipe-free setup modes therefore get the same clean
  setup-card visibility as built-in optical and CDSEM modes.
- The unified editor builder suppresses orphaned process-output drawing artifacts for recipe-free
  modes. Legacy process-output SVG/PNG/spec artifacts do not create Cross Sections navigator items
  unless the active mode is process-aware.
- Process-context warnings remain persisted for audit/diagnostics, but the unified editor filters
  them out for recipe-free modes. Dashboard warning counts and Warnings navigator items only include
  editor-visible warnings in simple, batch, CAD review, optical, CDSEM, and grid workflows.
- The global `ValidateSession` lifecycle command also reports only editor-visible warnings for
  recipe-free modes. Hidden process-context warnings remain persisted but do not make normal
  recipe-free session validation return a warning state.
- Capture CSV warning counts use the same recipe-free visibility rule. Hidden process-context
  warnings are not counted for simple, batch, CAD review, optical, CDSEM, or grid exports, while
  capture, measurement, and artifact warnings remain counted.
- Process-awareness checks are owned by the session domain, not by editor adapters. Setup commands,
  report readiness, diagnostics repair state, recipe-editor attachment, and editor presenters all
  use the same mode-policy predicate so recipe-free behavior does not drift across surfaces.
- Recipe-free report models use the same visibility policy as the editor and CSV. Warning summaries
  and session warning counts exclude hidden process-context warnings, and process-context summary
  data is omitted unless the active mode is process-aware.
- Recipe-free report artifacts use the same mode boundary. Legacy process-output artifacts and
  artifacts requiring recipe or solver repair are omitted from report galleries, artifact tables,
  report session-summary counts, capture/measurement artifact ref counts, and report readiness
  checks unless the active mode is process-aware.
- Recipe-free editor artifact summaries use the same artifact visibility rule. Legacy process-output
  artifacts are omitted from artifact health counts, per-item artifact details, capture artifact
  refs, capture inspector artifact status fields, and overview discovery unless the active mode is
  process-aware.
- Recipe-free dashboard missing-artifact counts use the same artifact visibility rule. Legacy
  process-output artifacts can remain in raw session JSON for audit, but they must not inflate the
  normal editor dashboard repair count for simple, batch, CAD review, optical, CDSEM, or grid modes.
- Recipe-free dashboard report readiness is derived from visible artifact statuses only. Visible
  missing or failed artifacts report missing required artifacts, stale artifacts report stale
  outputs, and placeholders or visible warnings report ready with warnings; hidden process-output
  leftovers do not change the normal recipe-free readiness status.
- Recipe-free dashboard CSV readiness is independent from report readiness. A stale or missing
  session-owned CSV export artifact updates the CSV readiness row but does not make report readiness
  stale, because reports can be built from the current canonical session and visible report-relevant
  artifacts.
- Recipe-free artifact previews use the same warning visibility rule when resolving artifact-path
  warnings. Hidden process-context warnings cannot turn an otherwise available capture image into a
  missing/error preview placeholder.
- Recipe-free render refresh uses the same artifact visibility rule when choosing base images for
  capture and measurement annotation scenes. Hidden process-output images cannot become the source
  layer for regenerated recipe-free annotations.
- Advanced Diagnostics keeps raw session data available through exported bundles, but visible
  artifact summary rows and missing-artifact counts follow the mode-aware artifact visibility rule.
  Legacy process-output artifacts do not make recipe-free diagnostics look broken or repairable.
- Advanced Diagnostics artifact validation action text uses the same visible artifact count,
  missing-artifact count, and repair-request count as the diagnostics summary. Raw registry totals
  remain available in debug bundles, not in normal recipe-free diagnostics status text.
- Advanced Diagnostics session validation status uses visible warning counts for recipe-free modes.
  Hidden process-context warnings do not make `ValidateSession` report a warning state, while
  structural validation issues and visible persisted warnings still do.
- Advanced Diagnostics warning summary rows and shell result counts use the same visible warning
  counts and codes for recipe-free modes. Hidden process-context warnings remain in raw debug
  bundle data, but they do not make normal diagnostics summaries look process-blocked.
- Advanced Diagnostics shell rendering uses a grouped dashboard projection over public summary rows.
  The controller appends session path, dirty state, solver backend, renderer backend, and report
  readiness rows at the app boundary where paths/editor document are available; the shell consumes
  `DiagnosticsDashboardModel` instead of inferring those states from widgets.
- Artifact scans preserve hidden process-only artifacts unchanged in recipe-free sessions. Scan
  summaries and repair candidates include only visible artifacts, so scanning a recipe-free session
  cannot create missing/stale process-output warnings or queue solver/recipe repairs.
- Recipe-free CSV artifact columns use the shared artifact visibility rule. Capture-owned legacy
  process-output artifacts are omitted from image paths and artifact status summaries unless the
  active mode is process-aware. Measurement artifact columns walk preferred refs until they find a
  visible artifact, so a hidden process-output `measurement_detail` ref cannot suppress a visible
  annotation artifact.
- User-triggered artifact manifest export also uses the shared artifact visibility rule. Recipe-free
  manifests and bulk repair candidate messages omit hidden process-only artifacts, while diagnostic
  debug bundles may still include raw registry data for audit.
- Drawing artifact ref synchronization is also mode-aware. Regenerating recipe-free capture drawings
  must not reattach legacy process-output artifact refs such as `stack_image` to the capture record.
- Pending compound capture metadata follows the same boundary. Recipe-free pending inspectors must
  not show process-context fields even if legacy compound metadata is present.
- Non-process mode validation accumulates all recipe, solver, setup, editor, artifact, and report
  leaks in one pass. Alternate process/recipe terms such as `recipe_setup`, `process_context`,
  `process_report`, and `stack_image` are treated as process-facing declarations.
- Session editor setup header fields and `Reopen Setup` primary actions are shown only for modes
  that declare a setup guide. Simple, fast-batch, CAD review, and other no-setup recipe-free modes
  should not display setup workflow affordances.
- Recipe-free report model building filters process-only sections after template/request/mode section
  merging. Optional selections such as `cross_section_gallery` cannot create process report sections
  for simple, batch, CAD review, optical, CDSEM, or grid sessions.
- CSV freshness signatures use the same recipe-free visibility boundary as CSV rows. Hidden
  process-output artifacts, hidden process warnings, and hidden owner artifact refs do not make a
  recipe-free capture CSV stale.
- Routine session-record validation follows the recipe-free visibility boundary for process context
  render profiles and process-output artifact refs. Raw diagnostic bundles may still include that
  hidden data, but normal project validation should not mark recipe-free sessions as broken because
  stale process leftovers exist.
- Advanced Diagnostics mode-policy rows use the same session-domain process-awareness predicate as
  editor and workflow surfaces. Stale process context on a recipe-free session cannot make
  diagnostics report the active mode as process-aware.
- Dashboard overview generation actions are mode-appropriate. Session overviews remain generic,
  metrology overviews are shown only for metrology-family modes, and grid overviews are shown only
  for modes that declare grid dataset support.
- Overview generation dispatch is guarded with the same mode policy as dashboard actions. Direct or
  stale UI dispatch cannot generate metrology overviews outside metrology-family modes or grid
  overviews outside grid-capable modes.
- Pending capture review actions must be routable through the shared command bridge. Measurements
  are added from saved capture parents, so pending captures do not expose a dead `take_measurement`
  action.
- Enabled visible editor actions for recipe-free modes must have either an app command route or a
  workflow dispatcher route. Overview user labels and capture copy actions are handled modelessly in
  workflow dispatchers so they remain available without adding blocking dialogs.
- The visible `Build Report` action is a real recipe-free workflow action. The app bridge opens the
  modeless Reporting Workbench, while the headless editor dispatcher generates the default report
  through the same reporting defaults and artifact registrar; without a session folder it returns a
  structured unavailable result instead of acting like a dead enabled action.
- Dashboard artifact lifecycle actions must work through both app-command routing and direct
  workflow dispatch. `Scan Artifacts`, bulk missing/stale repair, and artifact-manifest export all
  preserve the active recipe-free visibility boundary, so embedded editor shells do not need app
  command wiring to avoid dead dashboard buttons.
- Setup-guide action IDs are view-model commands, not free-form callbacks. Optical/CDSEM visible
  setup actions must normalize to registered app commands, and stale unknown action IDs return a
  structured setup-guide unavailable result rather than raising through the modeless UI.
- Saved recipe-free box captures must expose routable metadata, replacement, measurement,
  regeneration, CSV, and report actions without recipe/process controls. Non-box captures and
  legacy captures missing a saved canvas box keep measurement/replacement actions visible only with
  explicit disabled reasons.
- Stale pending-capture review actions are unavailable, not successful no-ops. Save, retake, and
  discard actions parse their pending id defensively and report that the pending capture is no
  longer available when a stale editor surface dispatches an old action.
- Grid dataset creation from the dashboard must be directly routable. When at least two saved box
  captures exist, the default action carries anchor IDs and conservative 1x1 counts so embedded
  editor surfaces do not expose an enabled action that immediately fails for missing payload; richer
  grid sizing can still override the payload.
- Grid dataset creation failures return the structured grid validation warning in the action result.
  Invalid anchor geometry or invalid row/column counts must be visible immediately to the editor
  caller, while the same warning is also kept in the session warnings list for navigator and
  diagnostics views.
- CDSEM capture metadata treats feature type as required and defaults it to `line`. Mode-declared
  capture-field defaults are persisted when pending captures are promoted, so CSV/report consumers
  do not need to infer required CDSEM metadata from inspector-only defaults.
- Saved recipe-free capture repair actions use image language. The normal capture action is
  `Regenerate Image`; drawing-specific labels are reserved for explicit session drawing items and
  measurement annotation artifacts.
- Recipe-free CSV warning counts apply the artifact visibility rule before following artifact
  warning IDs. Hidden process-output artifacts cannot inflate capture warning counts even when they
  carry otherwise visible artifact warnings.
- Artifact generators that update more than one canonical record return `ArtifactGenerationResult`
  instead of smuggling sibling writes through filenames or UI state. `ArtifactRepairService` uses
  the returned `SessionRecord` when present, then updates the requested artifact ID, preserving
  owner refs and central registry changes produced by render bridges or export services.
- Process-output artifact repair must declare recipe and solver requirements on
  `ArtifactRepairMetadata`. The repair queue should show missing recipe/solver as unavailable
  repair requirements, not as an available command that fails after dispatch.
- Generator declarations are not enough to make a repair action available. The repair service
  checks for a concrete registered handler and returns `GENERATOR_HANDLER_UNAVAILABLE` when the
  registry only documents the intended generator.
- Live layout crop repair is an app/host injection concern, not a headless default. The KLayout
  plugin supplies `KLayoutLayoutCropExporter` to `layout_crop_repair_service`; workflows keep using
  `ArtifactRepairService` and do not import `pya` or inspect live views directly.
- Artifact generator lookup prefers owner role before generic artifact type. Visual process
  artifacts often start as generic `process_output` records, so `profile_image`,
  `cross_section_image`, `full_stack_compressed_image`, `stack_image`, and `process_flow_frame`
  must route to role-specific solver/render SVG handlers before falling back to generic
  process-output JSON repair.
- Reporting output destination is an app/UI adapter concern. `ReportGenerationService` consumes a
  `ReportRequest.output_dir`; modeless shells choose that folder through `ReportOutputAdapter` and
  store it on the request before export.
- The visible mode catalog is narrower than the load-compatible registry. Legacy/internal/thin
  modes remain registered so saved sessions can open, but new-session pickers use
  `ModeRegistry.visible_mode_ids()`. `fib_cut_planner` is descoped until it can be implemented as a
  complete declarative mode, not added as a hollow placeholder.
- `process_flow_summary` is a hidden report-only/load-compatible mode, not a partial capture
  workflow. It preserves saved sessions and process-flow report template selection while forbidding
  recipe/solver workflow UI until a complete process-flow capture workflow is intentionally scoped.
- User-facing recipe-free mode names may have hidden load-compatible aliases when old or planning
  terminology differs from canonical saved IDs. `simple_labeled_capture` and `cad_review_capture`
  validate as recipe-free hidden aliases, while normal new-session selection continues to expose
  the canonical `simple_capture` and `cad_review` definitions.
- Setup-guide captures are setup-owned records, not normal pending captures. When the active
  workflow stage is origin point setup, the shared point capture path updates durable
  `SetupState.origin`. When the active stage is an origin reference, optical alignment, or SEM
  alignment setup stage, the shared box commit path creates a complete `SetupItemRecord` plus
  setup-owned image artifact request. Setup readiness can be reconstructed after save/reopen without
  modal review.
- Recipe-free saved captures always receive a central `site_image` artifact ref. If a pending
  capture is saved without an image path, save creates a capture-owned placeholder artifact plus a
  structured missing-artifact warning with a regenerate repair hint; CSV export can continue and
  reports can render the placeholder instead of blocking capture save.
- CAD review capture saves persist the same default review metadata shown by the editor. Missing
  review categories default to `layout_issue`, missing severity defaults to `medium`, and optional
  owner/assignee and tags stay generic pending metadata rather than requiring a CAD-specific review
  dialog.
- CAD review `review_annotation` artifacts are treated as normal capture annotations by the editor
  inspector and CSV export, so review markup uses shared readiness/status columns rather than a
  CAD-specific artifact path.
- Grid dataset editor items expose read-only planning metadata in the unified inspector, including
  anchor captures, row/column counts, planned site count, warning count, and grid-overview status.
  Grid planning should stay in the shared editor instead of gaining a mode-specific grid window.
- Recipe-free setup guide cards use explicit modeless setup action IDs for alignment captures.
  Optical setup routes through `StartOpticalAlignmentCapture`, CDSEM SEM setup routes through
  `StartSemAlignmentCapture`, and both commands still arm the shared box-capture primitive instead
  of adding mode-specific mouse handlers.
- External mode discovery is app-level and data-only via `MPP_MODE_DEFINITION_DIRS`. Loaded external
  modes are visible in diagnostics, and visible external registry IDs can be selected for new
  sessions. `SessionRecord.mode` remains compatible with built-in `SessionMode` values while
  allowing registered custom IDs as durable `SessionModeId` strings. App/editor construction must
  pass the active `ModeRegistry` into session stores, document builders, and editor adapters so
  external setup, action, measurement, and metadata policy can shape generic view models without
  executable custom code. Unknown unregistered saved mode IDs still fall back with structured
  `unsupported_mode` warnings.
- Measurement save remains a generic editor boundary, not a mode-specific review dialog. Saved
  measurements are revalidated against their parent capture during `SAVE_EDITS`: the parent must
  still be a box, both line endpoints must stay inside that box, and invalid geometry blocks save
  with the existing structured editor result instead of allowing stale or orphaned measurement
  records into recipe-free sessions.
- `AttachRecipe` is a shared app command ID, but routing is surface-aware. If the command comes
  from a routed Session Editor action, the editor payload path is used directly; otherwise the Setup
  Guide path-picker command handles process-aware setup attachment. Recipe-free sessions still
  receive the existing unavailable result rather than seeing recipe attachment as normal workflow.
- Advanced Diagnostics exposes explicit recipe-free workflow state rows. The summary reports setup
  state, capture state, and measurement workflow state in addition to mode policy rows, selected
  editor item, selected canvas object, command trace, warnings, and artifact health.
- Recipe-free CSV rows are treated as a user-facing contract, not a best-effort dump. Exports must
  continue to include capture geometry, center/size, nested measurement IDs/labels/types/lengths,
  target/LSL/USL, edge conventions, artifact status summaries, and warning counts without
  requiring recipe or solver context.
- Recipe-free capture tags are normalized at the unified editor boundary. Saved and pending capture
  tag edits accept comma- or semicolon-separated text but persist structured tag tuples so session
  JSON, CSV export, reporting, and diagnostics do not have to interpret raw UI strings.
- Recipe-free CSV export remains tolerant of legacy raw tag strings. Older sessions may already
  contain semicolon-delimited tag text, so CSV serialization preserves that value instead of
  treating the string as an iterable of characters.
- Simple labeled capture exposes `capture_type` as optional mode metadata alongside
  `capture_role`. The existing save pipeline already persists both values on the capture record and
  metadata map, so the editor should surface the type field instead of requiring users to rely on
  hidden defaults.
- Missing-artifact preview text is shared across unified editor previews and reusable pending-review
  preview widgets. Any missing, stale, failed, error, or placeholder artifact preview should state
  the problem, owning artifact/item role, CSV/report impact, and available repair action instead of
  showing a blocking dialog or terse missing-image label.
- Unified editor artifact refs preserve registry lifecycle states such as `failed`; warning severity
  may still surface as preview status `error`. Do not flatten failed artifact records to generic
  errors, because diagnostics, dashboard readiness, and repair previews need to distinguish artifact
  lifecycle from warning severity.
- Artifact repair actions must honor the selected artifact payload. The shared editor dispatcher
  validates that the artifact belongs to the selected capture or measurement, normalizes concrete
  drawing file roles such as `_spec`, `_svg`, and `_png` back to their render role, and only then
  routes regeneration through the render bridge. This keeps non-process repair actions precise
  without adding recipe, solver, or mode-specific repair dialogs.
- Normal site capture must respect setup policy for setup-heavy recipe-free modes. Optical and
  CDSEM captures are blocked by the shared canvas commit path until mode-declared required setup
  stages are complete, while setup-owned alignment/origin captures still commit through the shared
  setup capture path before that guard runs.
- Recipe-free `Add Capture` is a unified editor action that routes to the existing
  `StartCapture` app command. It should remain a modeless entry point into the shared box-capture
  primitive, not a mode-specific review dialog or mouse handler.
- Active capture cancellation is also a unified editor action. When durable workflow state is
  armed, the editor may show `Cancel Capture`, but it must route to the existing `CancelCapture`
  app command so fast-batch and normal capture exits share the same canvas/context cleanup.
- Fast Batch Capture honors the mode declaration `capture.review = false` in the shared box commit
  path. A Shift-drag still creates the normal pending capture and crop artifact internally, then
  immediately promotes it through `PendingCaptureReviewService` so sequence labels, site-image
  artifacts, canvas selection, and editor navigator state match the manual save path without adding
  a blocking review step.
- Fast Batch dashboard status is derived from durable workflow state rather than mode capability
  alone. Idle batch sessions report `ready` with saved/pending counts; armed sessions report
  `capturing`, and exit remains the shared `CancelCapture` primary action instead of a
  batch-specific command.
- CAD Review metadata is normalized at shared write boundaries. Pending promotion and saved
  metadata edits both constrain review categories to the mode-declared vocabulary and map invalid
  severities back to `medium`, keeping CSV/report rows stable without adding CAD-specific dialogs or
  recipe/process dependencies.
- Diagnostics is a first-class package, not an infrastructure adapter. The old
  `metrology_process_planner.infrastructure.diagnostics*` and
  `metrology_process_planner.infrastructure.trace_context` shim files have been removed; new
  diagnostics contracts, sinks, snapshots, seam checks, and trace helpers belong under
  `metrology_process_planner.diagnostics`.
- Process solver execution is separate from process recipe records. Recipe/material/step records
  remain under `domains.process`; solver orchestration, kernels, operations, profiles, outputs, and
  invariants live under `metrology_process_planner.solver`. Old
  `domains.process.<solver module>` shim files have been removed.
- Responsibility packages must contain real implementation files, not only facade `__init__.py`
  modules. Artifact, capture, measurement, mode, and warning domain files now live in their
  responsibility packages; old `domains.session.*` and flat `domains.measurements` shim files have
  been removed and are forbidden by `tools.audit_imports`.
- Canonical import paths are documented in `docs/CANONICAL_IMPORTS.md`; compatibility shims must be
  rare, quarantined, documented in `docs/COMPATIBILITY_SHIM_AUDIT.md`, and justified by a known
  external/public entrypoint before being introduced.
- Mode metadata fields may expose declarative option lists for editor controls. CAD review uses
  this to publish the review-category vocabulary from the mode definition, so the unified editor can
  present category choices without adding a CAD-specific dialog or workflow branch.
- Process recipe validation stays split by responsibility. `domains.process.validation` is the
  compatibility facade for public imports; structured message models, service orchestration,
  material checks, step checks, window checks, and scalar value helpers live in focused modules so
  recipe validation does not bypass the same size gates used for recipe-free mode hardening.
- Process-output regeneration is split into orchestration, execution, and output-extension helpers.
  `workflows.process_regeneration` remains the public command boundary, while solve/update mechanics
  and capture/process-output metadata builders live in focused modules that preserve the hard
  maintainability gates.
- Process recipe hardening is additive to the existing JSON and editor contracts. Rich material and
  step fields such as category, hatch style, physical role, notes, step name, and enabled state are
  serialized directly when present, while older minimal recipe JSON remains loadable. The legacy
  `ProcessRecipe.validate()` string API is preserved for existing callers; new editor, diagnostics,
  solver, and report-readiness code should use `RecipeValidationService` for structured severities,
  related material/step/layer targets, details, and repair suggestions.
- Process-aware output generation is session-owned, not a standalone recipe tool. `SolverInputBuilder`
  consumes `SessionRecord`, `CaptureRecord`, `ProcessContext`, and the attached `ProcessRecipe` to
  derive a normalized `ProcessOutputRequest` and solver input for ellipsometry point stacks,
  profilometry line profiles, FIB full-stack compressed views, and process-flow frames without
  depending on UI widgets.
- Solver/render unavailability must not block capture save or regeneration commands. When process
  outputs cannot be solved, `ProcessOutputService` ensures deterministic placeholder artifact records
  and a pending process-output manifest are present with structured warning IDs and repair metadata,
  so the unified editor, diagnostics, artifact repair, and reports can show process-output health
  from canonical session state.
- Process-output regeneration persists both the central artifact registry and the owning capture
  extension. `ProcessOutputRecord` remains the session-level output index, while ellipsometry,
  profilometry, FIB, and process-flow capture extensions store operation-specific summaries,
  solver-result refs, warning refs, and artifact refs for editor/report round-trips. The manifest
  artifact is registered for repair/reporting but filtered out of visual preview options.
- Advanced Diagnostics setup state is mode-aware for recipe-free setup modes. Optical and CDSEM
  sessions with declared setup cards report incomplete setup even before durable setup items exist,
  using the same setup-stage builder as the modeless guide, while simple and batch capture still
  report setup as not required.
- Grid measurement CSV export is additive to the capture summary export. Normal capture rows remain
  `row_kind = capture`; generated grid planned sites export as `row_kind = grid_site` rows with
  dataset id, row/column, center, anchor capture refs, overview artifact status, and warning count,
  without introducing recipe or solver dependencies.
- Grid measurement reports include a derived `grid_dataset` section. The section is declared by
  the recipe-free grid mode and built from canonical session grid datasets plus artifact registry
  status at report-export time, so grid report readiness can show planned site count, anchor
  captures, overview status, and warnings without adding process context or changing session JSON.
- Report template mode support treats built-in recipe-free aliases as their canonical modes.
  `simple_labeled_capture`, `cad_review_capture`, and legacy `cdsem_capture` sessions should pass
  the same report-readiness checks as `simple_capture`, `cad_review`, and `cdsem_measurement`
  respectively, without requiring process context.
- Setup-guide readiness is neutral workflow state, not process setup state. The shared
  `ready_for_capture` card now lives outside the process-stage module so optical, CDSEM, and other
  recipe-free setup modes can render readiness without importing recipe/process setup stages.
- Unified editor setup previews aggregate visible setup-owned artifacts. Origin/reference and
  optical/SEM alignment setup images should preview from the normal `Setup` navigator item, while
  process-only setup artifacts remain hidden for recipe-free modes through the shared artifact
  visibility policy.
- Recipe-free mode validation is the enforcement point for accidental process leakage. Built-in
  non-process modes must remain warning-free, and the validator must warn if a recipe-free mode
  declares recipe setup stages, process report sections, solver operations, process render profiles,
  or process-output artifacts.
- Fast Batch Capture uses batch-specific header language while retaining the shared capture command
  routes. Idle sessions show `Start Batch Capture`; active batch sessions show `Exit Batch Capture`
  and suppress the normal start/add action, so the operator has one clear workflow control without a
  mode-specific mouse handler or review dialog.
- Recipe-free setup cards prefer live canvas workflow status over persisted setup item status.
  Optical, SEM, origin point, and origin-reference setup captures show `waiting_for_canvas_capture`
  while the shared setup capture workflow is armed, including recapture over an already-complete
  setup item. This keeps the modeless guide aligned with the canvas without adding blocking dialogs
  or mode-specific capture handlers.
- Setup box capture commits are terminal workflow transitions. Once an optical alignment, SEM
  alignment, or optional origin-reference box is committed into a complete `SetupItemRecord` and
  setup-owned artifact, the shared capture arming is cleared so users return to the modeless setup
  guide/editor flow instead of staying in an accidental repeated capture state.
- Recipe-free setup readiness is a locked card until required setup stages are complete. The
  `Ready for capture` card shows a disabled `Mark Setup Complete` action with the missing required
  card labels instead of relying on an avoidable blocked command round-trip; direct commands still
  block for stale callers.
- Recipe-free setup capture readiness is visible from the session-editor header. Optical and CDSEM
  modes keep `Add Capture` visible but disabled until required setup cards are complete, using the
  same missing-card message as the shared `START_CAPTURE` command so users do not discover setup
  requirements only after a rejected drag or command.
- Grid Measurement planned sites are first-class workflow data, not export-only formatting. The
  grid dataset stores row-major planned-site IDs, labels, sequence numbers, row/column coordinates,
  and centers in `extensions["planned_sites"]`; editor fields, CSV rows, and report summaries reuse
  those persisted IDs with compatibility fallbacks for older anonymous planned-site entries.
- The post-measurement continuation prompt is a modeless unified-editor action surface. When a
  saved measurement is waiting for follow-up, the header primary actions are limited to `Take
  Another Measurement`, `Return to Editor`, and `Done`; each action routes through the shared
  command map instead of arming capture tools directly or opening a mode-specific dialog.
- Grid dataset creation is a unified editor action, not a grid-specific window. Grid-capable
  dashboards expose `Create Grid Dataset`; payload-bearing dispatch supplies two saved capture
  anchors plus row/column counts, then delegates to the shared grid workflow to create planned
  sites, overview placeholder artifacts, warnings, and the selected grid editor item.
- Grid validation warnings are structured around the selected anchor captures. Missing anchors,
  invalid row/column counts, non-box anchors, and overlapping anchors stay in the shared workflow
  and attach `capture:<id>` related item references, so the editor and diagnostics can surface the
  issue without process context or a blocking grid-specific dialog.
- Grid overview repair is dataset-owned. The `Regenerate Grid Overview` action on a grid dataset
  replaces that dataset's placeholder artifact in place, writes the SVG under `artifacts/grid/`,
  and clears the placeholder warning without creating a separate grid window, recipe dependency, or
  solver output.
- Shared compound capture plumbing is allowed for recipe-free modes only when it stays recipe-free.
  If a compound request declares `recipe_policy=forbidden`, `solver_operation=none`, no process
  artifact roles, and no process output key, save-time validation does not require process-output
  metadata and the saved capture extension omits process context, solver request, solver result,
  process-output placeholders, and missing-recipe warnings.
- CAD Review vocabularies are mode-declared editor metadata. Review category and severity options
  live with the recipe-free mode definition, while save-time normalization reuses the same constants
  so editor controls, CSV/report metadata, and validation stay aligned without a CAD-specific dialog.
- Pending capture promotion keeps canonical capture fields and self-describing metadata aligned.
  Saved recipe-free captures always write the final label, role, and type back into
  `metadata["label"]`, `metadata["capture_role"]`, and `metadata["capture_type"]`, so CSV/report
  adapters can treat the canonical capture record as the source of truth.
- CDSEM feature type is exported as first-class recipe-free CSV metadata. The CSV schema mirrors
  `capture.metadata["feature_type"]` in a dedicated `feature_type` column so CDSEM planning and
  measurement site lists do not hide site classification inside notes or require process output
  context to make reports useful.
- CDSEM capture-level measurement planning metadata is a CSV fallback until a nested measurement is
  saved. `measurement_type`, `target`, `lsl`, `usl`, and `edge_convention` are mirrored from
  capture metadata for planned sites with no measurement children; once a measurement exists, the
  measurement record remains authoritative for those columns.
- `Copy CSV Row` uses the canonical capture CSV row builder. The editor action mirrors the same
  columns as file export, including geometry, artifacts, warnings, CDSEM feature type, and
  measurement planning fields, instead of maintaining a compact hand-built row that can drift.
  adapters do not inherit stale pending-review metadata after an operator override.
- Saved capture label edits keep the same label mirror invariant. Editing a saved recipe-free
  capture label updates both `CaptureRecord.label` and `metadata["label"]` so CAD Review and other
  report/CSV consumers do not see stale metadata labels.
- Fast Batch rename is a payload-bearing unified-editor dashboard action. It is visible only in Fast
  Batch Capture mode, defaults to the existing `Capture 001` style, and rewrites saved capture labels
  through the shared dispatcher/rebuild path rather than adding a batch-specific dialog or handler.
- Fast Batch rename keeps capture metadata aligned with the canonical label. Renaming updates
  `CaptureRecord.label` and `metadata["label"]` together while preserving unrelated metadata so CSV
  and report adapters do not read stale labels.
- Recipe-free measurement type and edge-convention vocabularies live in the measurement domain and
  are surfaced by both CDSEM mode metadata and generic measurement editor fields. These options guide
  editor controls without rejecting legacy/custom strings during load or save.
- Measurement annotation colors are normalized to lowercase hex on save after validation. Operators
  may enter uppercase hex, but persisted measurement records, render styles, and artifact
  signatures use one stable representation.
- CDSEM feature type is also mode-declared as an option vocabulary. The list covers common line,
  space, contact/via, trench, alignment, overlay, and test-structure planning labels while preserving
  custom feature metadata as ordinary editable text. Recipe-free mode vocabularies live in a sibling
  mode vocabulary module so built-in mode construction stays below the maintainability size gate.
- Live KLayout UI coverage for recipe-free modes uses a seeded editor-region probe rather than
  manual inspection. The probe opens every built-in non-process mode with stale process context and
  process output records present, then asserts the real KLayout-backed editor header, actions, and
  navigator groups hide process context, cross-section groups, and recipe/process actions.
- Live KLayout setup-guide coverage also seeds stale process context for recipe-free metrology
  modes. Optical and CDSEM setup guides must render required optical/SEM alignment stages and
  readiness cards without recipe, process context, solver, stack, or profile language in the card or
  footer action surfaces.
- Advanced Diagnostics must identify the loaded mode definition and active canvas object, not only
  the raw session mode or selected editor id. Recipe-free support/debug views should show the active
  mode definition summary, selected item, selected canvas ids, and the mapped canvas object's type,
  workflow state, record id, and editor item id without surfacing recipe or solver state as required.
- `Edit Metadata` is a first-class unified-editor action for saved recipe-free captures and saved
  measurements. It routes to the existing metadata panel/selection path rather than opening a
  mode-specific dialog, while `Save Edits` remains the persistence action for applied field changes.
- Recipe-free dashboard artifact counts use precise labels. `Missing Artifact Count` counts only
  visible artifacts whose registry status is `missing`; `Artifact Attention Count` includes visible
  missing, failed, placeholder, and stale artifacts that may affect repair/report readiness.
- Recipe-free dashboard artifact repair actions use the same visible artifact statuses. `Regenerate
  Missing` and `Regenerate Stale` stay visible but are disabled with reason text when only hidden
  process leftovers or no matching visible artifacts exist.
- Recipe-free `Add Measurement` requires a saved box capture with a durable canvas object. The
  unified editor shows the action with a disabled reason when the parent cannot be armed, and the
  dispatcher returns a blocked result for stale direct calls instead of pretending measurement
  capture started.
- Recipe-free measurement parent failures use precise reason text. Missing capture records, non-box
  captures, and missing durable canvas boxes stay distinct in both disabled editor actions and
  direct dispatcher blocked results so operators can repair the actual parent-state problem.
- The `workflows` package facade must not eagerly import process-regeneration or solver code for
  recipe-free callers. Process-context workflow functions stay available as lazy exports, while
  non-process setup/capture imports can load without a solver backend or sampled-geometry modules.
- Recipe-free artifact visibility treats process roles as process-only even when legacy or external
  records use a generic image/SVG artifact type. Roles such as `stack_image`, `profile_image`,
  `cross_section_image`, and `full_stack_compressed_image` stay hidden from CSV, reports,
  dashboards, manifests, and repair counts unless the active mode is process-aware.
- Session editor header fields and primary actions consume the same adapter-backed mode registry as
  inspector fields and actions. External recipe-free setup modes therefore show setup status,
  `Reopen Setup`, and `Add Capture` without falling back to built-in-only process/setup inference.
- Recipe-free UI and dispatch policy should compare durable mode ids rather than enum object
  identity. Fast Batch labels and batch rename dispatch use `session_mode_value(...)` so open mode
  identifiers and normalized built-ins behave the same.
- Recipe-free mode validation treats process artifact roles as process outputs, even when a mode
  declares them as generic image/SVG artifacts. This keeps mode-definition guardrails aligned with
  CSV/report/artifact visibility so roles like `stack_image` and `cross_section_image` cannot leak
  into non-process-aware capture modes under a generic artifact type.
- Recipe-free artifact visibility also applies to concrete drawing-part role names. Generic legacy
  artifacts with roles such as `cross_section_svg`, `stack_image_png`, or `profile_image_spec`
  remain process-only and must not create cross-section/stack navigator items, dashboard counts, CSV
  rows, or report inputs in non-process-aware modes.
- Recipe-free artifact visibility normalizes external artifact type and role spellings before
  filtering. CamelCase, spaced, suffixed, or legacy labels such as `Stack Image PNG` and
  `CrossSectionImage` are treated like their canonical process roles at runtime, matching the mode
  validation guardrails.
- Pending measurement creation requires both a saved box canvas object and the corresponding saved
  parent capture record. Stale canvas overlays without a real capture must fail before creating a
  measurement canvas object, artifact placeholder, or nested measurement record.
- Modeless setup skip actions target the active optional setup card by stable stage id/type. The
  command must not skip the first unresolved optional setup item in storage, because saved setup
  items can exist out of card order after reopen, recapture, or external repair.
- Recipe-free CSV summaries include visible measurement-owned detail artifacts for every nested
  measurement in the capture-level path/status summaries. The singular measurement artifact columns
  remain first-measurement compatible, while `image_paths` and `artifact_statuses` provide the full
  capture artifact picture without requiring recipe or solver context.
- Missing, failed, stale, and placeholder previews should surface the artifact repair suggestion,
  not only the machine repair action id. `ArtifactRef` carries both so the preview can explain the
  repair path in operator language while dispatcher actions still route through stable command ids.
- Pending artifact previews are status placeholders, not blank available previews. Recipe-free
  capture/setup artifacts with `pending` or `pending_solver` status must explain ownership,
  export/report impact, and the repair/wait action until a present artifact replaces them.
- Pending capture editor items prefer canonical pending-capture artifact records over raw
  `image_artifact_path` fallbacks. This keeps pending review previews lifecycle-aware while still
  allowing older sessions without registry records to show a path-based preview.
- Recipe-free dashboard readiness treats pending artifact states as attention items. `pending` and
  `pending_solver` artifacts count in `Artifact Attention Count` and report `artifact generation
  pending`, while `Missing Artifact Count` stays limited to strictly missing artifacts.
- Artifact relink is a routed workflow action as well as an app command. Direct editor dispatch must
  return a precise unavailable result when no replacement path is supplied, and must update the
  canonical artifact record when `artifact_id` and `relative_path` payloads are present.
- Reusable preview-widget models preserve both artifact repair fields. Placeholder text may show the
  operator-facing repair suggestion, while `PreviewModel.repair_action` remains available to route a
  stable repair command from review/editor preview surfaces.
- Unified editor previews and reusable preview widgets share one artifact-role label map. Recipe-free
  setup images, optical/SEM alignment images, grid overviews, CSV exports, and report outputs should
  use operator-facing labels consistently instead of each surface re-title-casing machine roles.
- Advanced Diagnostics mode-policy rows use the active injected `ModeRegistry`, not only the
  built-in process-awareness predicate. External recipe-free modes must therefore report
  process-aware false, recipe-required false, solver-operation none, and process-context-visible
  false even when a session carries stale process context data.
- Session editor navigator groups are filtered and ordered through the active mode definition's
  `editor.navigator_groups` policy. The builder still indexes hidden records for repair and
  selection stability, but external and built-in recipe-free modes only surface the groups their
  loaded mode policy declares.
- Solver, render-profile, and process-output warnings are process-only even when their warning source
  is not `process_context`. Recipe-free editor, diagnostics, CSV, and reporting visibility filters
  must hide codes such as `SOLVER_BACKEND_UNAVAILABLE`, `RENDER_PROFILE_MISSING`, and
  `PROCESS_OUTPUT_STALE` so non-process modes do not surface solver or stack repair language.
- Non-process mode validation applies the same process-artifact role normalization used by runtime
  artifact visibility. Suffixed roles such as `cross_section_svg`, `stack_image_png`, and
  `profile_image_spec` are process outputs for guardrail purposes even when declared under generic
  image or SVG artifact types.
- Recipe-free setup readiness surfaces must not trust `setup.is_capture_ready` by itself for modes
  with required setup stages. Dashboard, setup guide, diagnostics, and capture arming should all
  treat stale ready flags as incomplete when required optical or SEM alignment items are missing.
- Generic capture commands enforce the same required-setup guard as canvas release. `Start Capture`
  and `Start Box Capture` return a blocked command result before arming site capture when optical or
  SEM required setup cards are incomplete, while setup-specific alignment capture commands remain
  available through the setup guide.
- Recipe-free CSV warning counts use mode-scoped warning visibility. Capture-related solver,
  render-profile, and process-output warnings remain hidden from CSV rows, while ordinary artifact
  and measurement warnings continue to count toward export/report readiness.
- Recipe-free CSV warning counts use the canonical artifact registry as well as local capture and
  measurement refs. Visible artifacts owned by a capture or nested measurement count toward row
  warning readiness even when a legacy record lacks a convenience back-reference; hidden process
  artifacts remain excluded.
- Saving a later recipe-free measurement must not reset existing measurement detail artifacts.
  Measurement save creates a repairable placeholder only when the nested measurement has no
  registered detail artifact; existing present, stale, failed, or placeholder detail artifacts keep
  their status and warnings for repair/report continuity.
- Fast Batch Capture status text uses batch-specific language while armed. The status strip should
  tell operators that Shift-dragged boxes auto-save and that `Exit Batch Capture` leaves batch mode,
  matching the header primary action instead of falling back to generic box-capture wording.
- CAD Review Capture CSV exports promote review triage metadata into stable columns. Review
  category, severity, and owner are written as `review_category`, `review_severity`, and
  `review_owner`, while tags continue to come from structured capture metadata.
- Editor warning visibility must honor the same injected mode registry used by navigator groups,
  dashboard fields, and action policy. External recipe-free modes therefore hide stale
  process-context warnings and do not count them in dashboard warning readiness.
- Grid Measurement keeps dataset creation in the dashboard but disables it until at least two saved
  box captures exist as anchors. The disabled reason is part of the editor action model, so normal
  grid setup stays modeless and avoids a failed command round-trip.
- Non-process mode validation treats `cross_section` and `cross_sections` navigator groups as
  process-output UI aliases. A recipe-free mode must use non-process overview, capture, measurement,
  grid, report, or warning groups instead of cross-section groups.
- Non-process mode validation normalizes external policy identifiers before checking for process
  leakage. CamelCase, hyphenated, spaced, or suffixed declarations such as `AttachRecipe`,
  `process outputs`, `cross-section-gallery`, or `Stack Image PNG` are treated as their canonical
  process-facing ids for guardrail warnings while preserving the original loaded mode data.
- Measurement metadata saves block malformed numeric and color edits before applying them. Invalid
  target/LSL/USL/line-weight text or non-hex annotation colors must produce visible blocked results
  instead of silently preserving the previous measurement value.
- Measurement spec-order edits also block before mutating the canonical session in the returned
  editor document. Pending edits are overlaid for validation, and invalid `LSL <= target <= USL`
  relationships leave the last valid measurement record intact until the operator corrects the
  metadata.
- Advanced Diagnostics dashboard includes an explicit Mode Policy section. Recipe-free sessions must
  visibly report loaded mode definition, process-aware false, recipe-required false, solver
  operation none, process-context-visible false, setup state, capture state, and measurement state.
- Advanced Diagnostics uses mode-aware dashboard sections. Process-aware modes keep the combined
  process/report card group, while recipe-free modes expose report readiness in a report-only group
  so solver backend, renderer backend, and recipe-context cards do not reappear in normal
  non-process diagnostics.
- Recipe-free dashboard report readiness distinguishes missing, failed, stale, and placeholder
  artifact states. Missing artifacts report `missing required artifacts`, failed artifacts report
  `artifact repair required`, stale artifacts report `stale outputs`, and placeholders remain
  `ready with warnings`.
- Saved-capture visual regeneration actions are role-specific. Recipe-free captures still expose a
  generic image regeneration/repair path, but overview and annotation refresh commands only appear
  when the selected capture actually owns those artifact roles, keeping the editor action list tied
  to visible outputs instead of advertising unrelated process or visual placeholders.
- Advanced Diagnostics setup state uses the same required-stage readiness rule as the setup guide.
  A recipe-free setup mode may report `ready` when required alignment stages are complete and
  optional setup cards remain unfinished, but stale `is_capture_ready` flags are still incomplete
  when required optical or SEM alignment records are missing.
- `HybridCrossSectionSolver` instantiates `AdvancedGeometryKernel`, a facade over the deterministic
  sampled-column backend. This keeps the public pipeline aligned with `ProcessRecipe -> SolverInput
  -> AdvancedGeometryKernel -> SolverResult -> RenderProjection -> CrossSectionScene` without adding
  an unapproved geometry dependency. Conformal coating remains a sampled exposed-surface growth
  approximation with explicit conformal-layer, coverage-factor, thin-layer, and pinch-off metadata;
  directional, isotropic, and tapered etches now honor mask intervals in the kernel and record
  undercut or tapered-opening metadata for renderers. Renderers consume these advanced geometry
  records only through `RenderProjection` on process frames, not solver-private state.
- Report items in the unified editor expose artifact-specific regenerate and relink actions through
  the shared artifact repair action builder. Recipe-free report outputs stay repairable from the
  normal editor surface without a report-specific dialog or process-output navigator group.
- Report items also expose read-only inspector metadata from the canonical `ReportRecord`: label,
  report type, status, generated timestamp, artifact count, and warning count. This keeps generated
  recipe-free reports understandable from the unified editor without adding a separate report
  details window.
- Report artifact preview labels use the report-owned artifact type when the owner role is
  `report_output`, so PowerPoint decks, PDF reports, CSV exports, image bundles, and manifests are
  distinguishable in both the unified editor preview and reusable preview widgets.
- Report artifact regeneration from the unified editor routes through `ArtifactRepairService` using
  the selected report artifact id. It must not fall through to drawing refresh or process-output
  regeneration, so recipe-free report repair stays artifact-lifecycle based and modeless.
- Report-owned exports use the `report_export` artifact generator for repair, including report CSV,
  PDF, image bundles, and manifests. A report-owned `csv_export` artifact is a report rebuild, not a
  session capture CSV rebuild, even though both share the `csv_export` artifact type.
- Dashboard CSV readiness is owner-specific. Only session-owned `csv_export` artifacts represent the
  capture CSV export; report-owned CSV outputs remain report artifacts and affect report readiness
  instead of making capture CSV readiness look ready or stale.
- The unified editor Setup navigator item has its own lightweight inspector and action surface. It
  shows setup status, current stage, completed-stage count, incomplete required cards, and setup
  artifact count, and exposes `Reopen Setup` instead of inheriting dashboard overview/scan actions.
- Setup-owned artifacts expose regenerate and relink actions from the unified setup item. Regenerate
  routes through `ArtifactRepairService` by selected setup artifact id, so missing setup reference,
  optical alignment, and SEM alignment artifacts remain visible and repairable without process
  context or setup-specific dialogs.
- Measurement inspector fields use the user-facing `edge_convention` key to match mode definitions,
  CSV export, and metadata edit commands. The persisted `MeasurementRecord` field remains
  `edge_detection_convention`; adapters translate at the editor boundary.
- Advanced Diagnostics treats grid measurement state as recipe-free workflow state. Grid dataset
  count, planned-site count, and grid overview artifact statuses appear alongside setup, capture,
  and measurement rows, so grid readiness is visible without exposing process context or solver
  outputs.
- Grid overview diagnostics resolve artifact status through the active `ModeRegistry`. Hidden
  legacy process artifacts referenced by old grid datasets do not leak stale process-output status
  into recipe-free diagnostics; the visible recipe-free grid overview is reported as missing until a
  normal grid overview artifact or placeholder exists.
- Grid report summaries use the same active `ModeRegistry` visibility boundary as CSV and
  diagnostics. Hidden legacy process artifacts and process warnings referenced by old grid datasets
  remain preserved in JSON but do not populate recipe-free report grid rows, report warning lists,
  or report artifact galleries.
- Warning repair actions use the active editor `ModeRegistry` when deciding whether process repair
  actions are allowed. External recipe-free modes must not synthesize Attach Recipe, Validate
  Process Context, or Regenerate Process Output from warning rows, even if a stale process warning is
  addressed through a direct adapter call.
- Modeless setup commands use the active application `ModeRegistry` for required-stage checks,
  optional-stage skipping, and recipe-validation availability. Configured recipe-free setup modes
  therefore follow their loaded setup policy without falling back to built-in mode assumptions or
  exposing recipe/process validation commands as normal workflow steps.
- Dashboard artifact readiness and dashboard repair-action counts use the active editor
  `ModeRegistry` when filtering process-owned artifacts. External recipe-free modes therefore keep
  stack/profile/process-output artifacts hidden from missing-artifact counts, report readiness, CSV
  readiness, and repair buttons without requiring a built-in mode id.
- Normal capture readiness uses the active loaded `ModeRegistry` from both modeless capture commands
  and canvas release. External recipe-free setup modes with required optical or SEM setup stages
  must block site capture until those required setup cards are complete, matching built-in optical
  and CDSEM behavior without requiring a built-in mode id.
- Recipe/process attachment and process-context editor actions use the active loaded `ModeRegistry`
  before mutating session process context. External recipe-free modes must reject setup-guide recipe
  attachment, recipe-editor attachment to active session, and direct attach/detach/validate/
  regenerate editor dispatches with recipe-free unavailable results.
- Unified editor metadata fields, header capture readiness, recipe-context state, and artifact repair
  state use the active adapter or diagnostics `ModeRegistry`. Recipe-free configured modes therefore
  hide process metadata, process-context states, process-output repair actions, and setup-blocked
  capture affordances consistently across external mode ids and built-in mode overrides.
- Report model building, readiness checks, headless generation, and the modeless reporting workbench
  use the active `ModeRegistry` when filtering process sections, process warnings, process-context
  summaries, and process-owned artifacts. External recipe-free modes must not regain process report
  sections or missing-process-context blockers through default reporting helpers, even when their
  session mode id looks like a built-in process mode.
- Capture CSV export, capture CSV row copy, artifact-status columns, measurement artifact columns,
  and warning counts use the active `ModeRegistry` when filtering process-owned artifacts and
  process warnings. Loaded recipe-free modes therefore keep CSV output recipe-free even if their mode
  id would otherwise match a built-in process-aware workflow.
- Editor item artifact refs, artifact detail rows, artifact health counts, orphaned drawing items,
  and artifact-specific repair/relink action payloads use the active `ModeRegistry` before exposing
  artifacts to the unified editor. Loaded recipe-free modes therefore cannot surface stack/profile/
  cross-section artifacts through capture, measurement, overview, report, or drawing rows simply
  because those artifacts are still present in legacy session JSON.
- The unified editor header resolves setup state through the active adapter `ModeRegistry`, matching
  the Add Capture readiness guard and setup guide presenter. Loaded recipe-free setup modes with
  required optical or SEM alignment stages must not show a ready setup state just because an old
  `is_capture_ready` flag is true while required setup cards are incomplete.
- Advanced Diagnostics warning counts, warning-code summaries, artifact summaries, missing-artifact
  counts, artifact repair queue summaries, and artifact registry validation actions use the active
  `ModeRegistry`. Loaded recipe-free modes therefore confirm the same recipe-free artifact/warning
  visibility as the editor, CSV, and reporting surfaces instead of falling back to built-in process
  assumptions.
- Advanced Diagnostics validation actions also use the active `ModeRegistry` when counting persisted
  warnings. A loaded recipe-free mode with hidden legacy process-context warnings should validate as
  clean when no visible structural/session warnings remain.
- Artifact scanning and diagnostics artifact health reports accept the active `ModeRegistry` when
  deciding which artifacts are visible to normal recipe-free workflows. Loaded recipe-free modes must
  preserve hidden legacy process artifacts in session JSON without marking them missing, stale, or
  repairable in operator-facing scan results.
- Measurement save creates a visible `measurement_detail` placeholder when the existing
  `measurement_detail` reference points only to a hidden process artifact. Legacy stack/profile
  artifacts may remain in session JSON, but they must not satisfy the recipe-free measurement detail
  contract or suppress the repairable measurement placeholder.
- Session metadata edits invalidate derived artifacts through the canonical artifact registry, not
  through transient editor state. Capture and measurement edits mark owned visuals, dependent CSV
  exports, report artifacts, and `ReportRecord` status stale; regeneration remains the existing
  artifact repair/generator workflow.
- Artifact scanning treats file presence and freshness as separate states. A present file can clear
  a missing warning, but it must not turn a deliberately stale artifact back to present; only a
  successful regeneration should clear stale status and update dependency metadata.
- Capture review policy, auto-save promotion, and pending capture defaults use the active
  `ModeRegistry`. Loaded recipe-free batch modes can therefore skip review and apply their own
  sequence labels, capture roles, and capture types without relying on built-in mode ids.
- Artifact scan, bulk repair, report-workbench artifact repair, and post-export document rebuilds
  use the active `ModeRegistry`. Loaded recipe-free overrides for process-named modes must preserve
  hidden process artifacts without surfacing unavailable recipe/solver repair warnings after normal
  report or repair actions.
- App-level document refreshes after measurement-completion choices, layout binding, and active
  session refresh use the active editor `ModeRegistry`. Loaded recipe-free overrides must not regain
  process warning visibility after normal workflow commands rebuild the unified editor document.
- The modeless setup guide presenter uses the active application `ModeRegistry`, matching setup
  command execution. Loaded recipe-free setup modes must show their configured setup cards and mode
  display name instead of falling back to unsupported/default built-in setup stages.
- Setup-guide actions re-render the already-open modeless window after command routing. Normal setup
  choices must update the visible active card, status, and action list immediately without requiring
  the operator to reopen the guide or accept a blocking dialog.
- App-level CSV export commands must preserve the active editor `ModeRegistry` through command
  routing, CSV row generation, document rebuild, and dashboard readiness. Loaded recipe-free
  overrides for process-named modes must not surface hidden process artifacts or process readiness
  after a toolbar/menu CSV export.
- Editor artifact previews, setup artifact refs, overview discovery, capture artifact inspector
  fields, and render-refresh source image selection use the active `ModeRegistry` before exposing or
  consuming artifacts. Loaded recipe-free overrides may keep legacy process artifacts in canonical
  JSON, but those artifacts must not become preview tabs, setup refs, overview items, inspector
  statuses, or annotation base images.
- Warning rows and warning-derived repair actions use the active `ModeRegistry` when resolving
  related artifacts. Artifact warnings whose only related artifacts are hidden process outputs must
  stay out of recipe-free warning counts and must not offer generic regenerate/relink actions through
  direct adapter calls.
- Measurement save uses the active `ModeRegistry` when deciding whether an existing
  `measurement_detail` artifact satisfies the recipe-free measurement contract. Hidden legacy
  process-output artifacts may remain referenced in old JSON, but they must not suppress creation of
  a visible pending measurement-detail artifact and repair warning.
- Pending measurement ID generation reserves IDs from nested measurement records and unsaved
  measurement canvas lines. Repeated measurement drags before save must produce stable unique
  measurement IDs and matching canvas record IDs.
- Pending measurement creation validates the canonical parent `CaptureRecord.geometry`, not only
  the visible canvas object. A child measurement line may only be added when the saved parent capture
  is a box; stale or inconsistent canvas boxes must not create measurements under point/line
  captures.
- Advanced Diagnostics exposes measurement workflow state, active target, and available workflow
  actions. Armed and pending measurement states must be explainable from diagnostics without opening
  raw session JSON.
- Recipe-free Advanced Diagnostics derives solver and renderer backend rows from mode policy, not
  stale `process_context` data. If the active mode is not process-aware, diagnostics must report
  `Solver Backend = none` and `Renderer Backend = none` even if legacy session JSON still carries
  recipe, solver, or render-profile fields.
- App-level line-capture commands follow the same measurement policy as the unified editor
  `Add Measurement` action. Measurement line capture must stay blocked unless the active mode
  supports measurements and a saved box capture is selected.
- Non-process mode validation treats process-output manifest/json/csv aliases as process artifacts.
  External mode declarations such as `process_output_manifest`, `process-output-json`, or
  `Process Output CSV` must warn before they can leak process-output artifacts into recipe-free
  capture workflows.
- Non-process mode validation treats singular and plural process regeneration commands, recipe-file
  open commands, and normalized action aliases as process UI. External recipe-free modes must warn
  on actions such as `Regenerate Process Outputs`, `Open Recipe File`, or
  `validate-process-context`.
- Non-process mode validation treats singular and plural process-output navigator groups as process
  UI. External declarations such as `Process Output` and `Process Outputs` must both warn before
  they can surface recipe/solver concepts in recipe-free editors.
- Report inspector artifact/warning counts and Advanced Diagnostics report-readiness rows use the
  active `ModeRegistry` before counting report artifacts. Loaded recipe-free overrides may preserve
  legacy process report refs in JSON, but those hidden refs must not make reports look ready or add
  process warnings to recipe-free report metadata.
- Recipe-free dashboard readiness ignores superseded and intentionally ignored artifacts. Replaced
  or dismissed records remain in canonical JSON and artifact health history, but they must not count
  as current CSV/report readiness, missing-artifact, or repair-attention work.
- Grid planned-site CSV rows use the active `ModeRegistry` for overview artifact and warning
  visibility, matching capture rows. Loaded recipe-free overrides for process-named modes must not
  expose legacy stack/profile/process artifacts through grid overview CSV columns.
- Setup inspector artifact counts use the same visible setup artifact refs as previews and repair
  actions. Hidden legacy process artifacts may stay referenced by setup JSON, but they must not
  inflate recipe-free setup metadata or suggest missing process setup work.
- Artifact relink follows the same active `ModeRegistry` visibility rule as scan and regenerate.
  Stale direct payloads naming hidden process artifacts must return unavailable/no-op results in
  recipe-free sessions instead of mutating legacy process-output paths.
- Artifact invalidation follows the same active `ModeRegistry` visibility rule before marking
  artifacts stale. Loaded recipe-free overrides must not turn hidden legacy process artifacts stale
  during ordinary label, metadata, save, or measurement edits; visible CSV/report/session artifacts
  still become stale through the shared lifecycle path.
- Artifact scan summaries, session-data freshness signatures, and drawing artifact-ref sync use the
  active `ModeRegistry`. Loaded recipe-free overrides for process-named modes may preserve legacy
  process artifacts and warnings in session JSON, but those hidden records must not count in scan
  summaries, make visible recipe-free artifacts stale, or reattach stack/profile refs to captures
  after annotation rendering.
- Report artifact registration stores `session_data` dependency signatures through the active
  `ModeRegistry`, matching scanner freshness checks. Hidden legacy process artifacts may remain in
  saved recipe-free sessions without making freshly exported report decks, manifests, or bundles
  immediately stale.
- Capture CSV export registration stores `session_data` dependency signatures through the active
  editor `ModeRegistry`. A recipe-free CSV exported from a loaded override must stay fresh when only
  hidden legacy process artifacts or process warnings change.
- Artifact repair generator handlers may opt into the active `ModeRegistry`. CSV and report repair
  rebuilds must use the same recipe-free visibility, row generation, report modeling, and dependency
  signatures as explicit export commands.
- Editor artifact placeholder previews prefer canonical owner context such as `capture cap-001`,
  `measurement meas-001`, `grid_dataset grid-001`, or `report report-001` over raw artifact ids.
  This keeps missing/stale/failed previews tied to the affected session item while preserving the
  raw artifact id as a fallback for reusable preview widgets and standalone artifact refs.
- Measurement inspector fields use recipe-free operator vocabulary: `lsl`, `usl`, and `color`.
  Canonical records still store `lower_spec_limit`, `upper_spec_limit`, and `annotation_color`, and
  edit application continues to accept legacy aliases, but normal editor view models should expose
  the concise workflow terms used by measurement CSVs and mode metadata.
- Capture inspector fields expose `capture_role` and `capture_type` as the operator-facing capture
  classification terms. Pending captures show the resolved saved-capture role from mode policy
  rather than the low-level canvas primitive, and saved-capture role/type edits update the canonical
  `CaptureRecord.role` / `CaptureRecord.type` fields as well as metadata mirrors.
- Pending capture review actions stay scoped to the pending capture workflow: save, retake, discard,
  CSV export, and report build. Closing or ending the editor session remains a header/lifecycle
  command, not an inspector action that appears to modify the pending capture but only returns a
  generic close request.
- Optical and CDSEM setup guides expose only recipe-free setup commands. Coordinate, origin
  reference, optical alignment, SEM alignment, skip, completion, and return actions are valid;
  attach/validate/open recipe actions must stay out of these setup cards and modeless command rows.
- Non-process mode validation treats recipe-reference setup stages and recipe fingerprint refresh
  actions as process-context leaks. External recipe-free modes must warn on `recipe_reference` setup
  stages and `Refresh Recipe Fingerprint` actions before they can surface stale recipe maintenance
  UI in capture-only workflows.
- App-level process commands may remain globally registered for menu/shortcut consistency, but the
  active session editor route is still mode-scoped. In recipe-free sessions, direct `Attach Recipe`,
  `Detach Recipe`, `Validate Process Context`, and `Regenerate Process Output` command invocations
  must return structured unavailable results and leave legacy process context, warnings, and process
  outputs unchanged.
- Recipe-free editor action sweeps must iterate the registered non-process mode definitions rather
  than a hand-maintained canonical subset. Hidden load aliases such as `simple_labeled_capture`,
  `cad_review_capture`, and `cdsem_planning` still need routable, process-free editor actions when
  old sessions are opened.
- Recipe-free CSV warning counts must apply artifact visibility before relating artifact warnings to
  capture or measurement rows. Hidden legacy process artifact refs may remain in capture JSON, but
  generic artifact warnings such as `ARTIFACT_MISSING` for those hidden refs must not inflate
  capture `warning_count` or make CSV/report readiness look worse.
- Bulk artifact repair actions are visibility-scoped. Recipe-free `Regenerate Missing` and
  `Regenerate Stale` actions may scan sessions that still contain legacy process artifacts, but they
  must count and repair only visible recipe-free artifacts and must not add recipe/solver repair
  warnings to hidden process records.
- Optical and CDSEM setup readiness is durable session state, not transient guide UI state. Completed
  required setup items plus `is_capture_ready=True` must survive `session.json` save/reopen and
  rebuild the guide directly into `setup_ready` for canonical `optical_metrology` and
  `cdsem_measurement` sessions.
- Hidden recipe-free load aliases must keep full workflow parity even when they are not shown in new
  session pickers. Loaded `cdsem_planning` sessions use the same CDSEM setup commands, optical/SEM
  readiness guards, CSV columns, copy-row behavior, and report template support as
  `cdsem_measurement`.
- Editor action modules must not import the reporting service at module import time. Report
  generation stays behind the `Build Report` action handler so lightweight report-template imports
  do not form a reporting/editor circular import.

## Visual Review Decisions

- `tests/output/visual_review_gallery/manifest.json` is the canonical visual QA
  inventory for generated test visuals.
- SVG plus scene JSON is the review source of truth for this pass; PNG rasterization
  remains optional until a stable rasterizer is configured.
- Structural visual checks live under `metrology_process_planner.testing` so they can
  be reused by tools and unit tests without coupling production renderers to tests.
