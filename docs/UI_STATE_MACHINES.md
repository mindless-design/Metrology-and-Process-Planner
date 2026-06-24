# UI State Machines

Last updated: 2026-06-24

The modeless UI renders from pure workflow state snapshots. Widgets should not infer workflow state from scattered booleans, window state, or raw JSON. The current alpha spine has these evaluators:

| State machine | Source data | Purpose |
| --- | --- | --- |
| `SessionUIStateMachine` | `SessionRecord` | Editor/dashboard state: idle, active workflow, or pending review. |
| `SetupGuideStateMachine` | `SessionRecord` plus `ModeDefinition` | Setup checklist stage, active setup card, warnings, and command intents. |
| `CaptureInteractionStateMachine` | `InteractionContext` plus optional `SessionRecord` | Armed primitive, live preview, or pending review gesture status. |
| `PendingReviewStateMachine` | `SessionRecord.pending_captures` | Pending simple/compound capture review actions. |
| `MeasurementWorkflowStateMachine` | `SessionRecord.workflow` plus nested measurements | Measurement line arming and pending measurement review actions. |
| `RecipeContextStateMachine` | `SessionRecord.process_context` | Recipe attached, missing, or warning status for editor headers. |
| `ArtifactRepairStateMachine` | `SessionRecord.artifacts` | Missing, stale, failed, pending, or solver-pending artifact repair state. |

## Command Flow

State-machine snapshots expose command-shaped action IDs. UI shells should route those IDs through `CommandRouter`, which returns a structured result containing:

- `status`
- `message`
- `updated_document_id`
- `selected_item_id`
- `warning_ids`
- `next_ui_hint`

The KLayout Tools menu uses only the primary `MENU_COMMANDS`; setup cards, recipe cards, editor buttons, and review actions use the broader typed command catalog.

## Window Ownership

`WindowRegistry` is the modeless surface owner for the primary product windows. Controllers open or
refresh surfaces through `get_or_create_session_editor`, `get_or_create_setup_guide`,
`get_or_create_recipe_editor`, and `get_or_create_diagnostics_panel`; the generic lifecycle backend
still owns toolkit-specific alive/raise behavior. This keeps duplicate-window prevention,
bring-to-front behavior, diagnostics keys, and shell refresh callbacks in one place.

The session editor keeps document mutation in `EditorActionDispatcher`, but app-owned header
intents are bridged into the app command router. `Save Edits` maps to `SaveSessionEdits`, whose
handler delegates back to the active editor dispatcher and returns a structured command result with
the updated document/selection IDs. `Reopen Setup` maps to `OpenSetupGuide` after handing the
active editor session to the setup guide, and editor `Close` maps to `EndActiveSession` so the
same blocked/diagnostic behavior is used from menus and editor buttons.

Selected-item editor commands use the same bridge. Commands such as `SavePendingCapture`,
`RetakePendingCapture`, `DiscardPendingCapture`, `SaveCompositeCapture`, `AddMeasurement`,
`SaveMeasurement`, `RetakeMeasurementLine`, `DiscardMeasurement`, `RegenerateArtifact`, and
`RegenerateProcessOutput` resolve the active `SessionDocument` selection, delegate to the matching
editor action, then return command metadata for the refreshed document and selected item. This
keeps future menus, shortcut handlers, and widget buttons on one modeless command path.

Process-context editor commands follow that route too. When a widget emits a payload-bearing action
such as `AttachRecipe` with a recipe path, the controller preserves that action while
`CommandRouter` runs, so the command service can delegate the same payload to
`EditorActionDispatcher`. Direct command invocations without required payloads return structured
unavailable results rather than opening modal file prompts.

`TakeAnotherMeasurement` is also a command, not a widget-side continuation. The command applies the
allowed post-measurement completion choice to the active editor document, selects the parent
capture, and rearms measurement-line capture state. If no saved measurement is available, it
returns `unavailable` and leaves the document unchanged.

`Open Output Folder` is a modeless shell handoff. The dispatcher resolves the configured session
folder into `EditorActionResult.output_path`; UI adapters may reveal that path, but workflow code
does not launch external applications or block on missing folders.

`ExportCSV` and `OpenOutputFolder` now enter through app commands before reaching the editor
dispatcher. Their path handoffs are mirrored on `CommandRouteResult.output_path`, so future Qt
shells can expose the path without bypassing command tracing or diagnostics.

Generic capture commands use the same modeless command route as setup actions. `StartCapture`
aliases box capture; explicit box, line, and point commands arm `CanvasInteractionEngine`, write
durable `WorkflowState` on the active session, and refresh any open editor/setup surfaces for that
session. `CancelCapture` clears ephemeral interaction context and durable workflow arming without
discarding saved records.

`EndActiveSession` is a modeless lifecycle command, not a blind close. It may clear the active
editor, setup guide, diagnostics session, and capture arming only when there are no dirty editor
edits and no pending capture review items. Dirty or pending state returns `status="blocked"` with a
next-action hint, and `CommandRouter` records the blocked command as a warning diagnostic.

Setup guide stage actions are emitted as command IDs by the pure presenter and routed by the
`SetupGuideController` through the shared `CommandRouter`. Setup capture commands arm shared
canvas primitives and update durable `WorkflowState`; setup configuration commands update
canonical setup fields. `SkipOptionalSetupStage` marks the first incomplete explicit optional setup
item as skipped, and `ValidateRecipeContext` runs the process-context validation workflow so recipe
warnings appear inline through session warnings instead of prompts. Deferred setup commands should
return structured unavailable results; they
should not become widget-local logic or blocking prompts.

Setup guide cards expose `SetupActionViewModel` rows for primary, secondary, and footer actions.
Those rows carry command ID, label, enabled state, and disabled reason, so card widgets can show
available and blocked actions without hard-coded command labels or modal fallback prompts.
Cards also expose `requirement_badge` and `artifact_badge`; shells should render those fields
directly instead of rechecking setup metadata or artifact registry records.

Advanced Diagnostics actions follow the same modeless pattern. The shell renders
controller-provided `EditorActionViewModel` rows and stores a generic action callback; dispatch
returns a typed result with status, message, optional text, and optional output path. Diagnostics
actions should resolve paths or validation summaries for the shell, not open modal file browsers or
launch external applications directly.

Disabled editor actions carry `disabled_reason` in the same view model as their command ID. UI
shells should render disabled actions with that reason, and dispatch should return the same reason
as a structured `unavailable` result rather than silently doing nothing.

The session editor navigator may be filtered by search text or warning severity, but filtering is
modeless shell state. The shell receives grouped filtered rows and a filter callback; it should not
mutate `SessionDocument` or persist search state into session JSON.

Recipe editor card/header actions use `RecipeEditorActionDispatcher` before any widget-specific
behavior. The dispatcher converts action IDs such as `AddProcessStep:directional_etch` to typed
commands, applies safe in-memory recipe edits, and returns structured unavailable results for
deferred save/open/attach workflows. The modeless recipe editor shell exposes a generic action
callback; widgets should call that callback rather than mutating recipe state directly. Closing the
recipe editor is a controller/window-registry action, not a recipe mutation.

Process-step cards expose their own status label and card actions. The selected-card detail panel
uses the same shared action policy, so enable/disable visibility and movement actions stay
consistent between the card list and detail panel.

Dirty recipe close is a modeless blocked state: `CloseRecipeEditor` returns a structured result
when unsaved edits exist and leaves the window open. A future destructive-confirmation widget may
dispatch `CloseRecipeEditor:discard` to close after the user confirms data loss.

`SaveRecipe` is handled at the recipe editor controller/service boundary, not inside widgets. A
recipe with `metadata.recipe_path` is written through `ProcessRecipeJsonStore`; successful saves
clear dirty metadata, while save failures return structured `error` results and keep edits in
memory.

`SaveRecipeAs:<path>` follows the same modeless service path and updates `metadata.recipe_path`
after a successful save. The eventual file-picker UI should dispatch the path-bearing command
instead of writing files itself.

`NewRecipe` and `OpenRecipe:<path>` are dirty-safe modeless switch actions. If the current recipe
has unsaved edits, they return a structured `blocked` result. A confirmation widget may dispatch
`NewRecipe:discard` or `OpenRecipe:discard:<path>` after the user accepts losing unsaved edits.

Recipe editor selection should render through `selected_detail` on `RecipeEditorViewModel`.
Material, process-step, and layer cards expose their own field/action models there, keeping card
selection and detail editing on the same modeless view-model spine.

Recipe editor header state renders through `RecipeHeaderViewModel`. The presenter derives recipe
path, dirty state, validation status, warning count, and attach readiness from recipe metadata and
validation output; header buttons carry disabled reasons for unloaded, unsaved, or dirty recipes.

Recipe material deletion is handled as an inline action result: unused materials may be removed
from the in-memory recipe and mark it dirty, while materials referenced by process steps return a
structured `blocked` result with warning IDs and repair guidance.

Recipe material add, duplicate, visibility toggle, and usage lookup use command-shaped action IDs.
Mutating material actions mark the recipe dirty and keep the material card selected. Usage lookup
returns a modeless result message and should not dirty the recipe.

Recipe material detail edits use `EditMaterial:<material_id>:<field>:<value>` action IDs. Domain
fields update the selected `Material`; category and notes update the recipe metadata extension
blocks. The workflow marks the recipe dirty and returns inline errors for malformed payloads.

Recipe validation rows are clickable modeless view models. When a validation message can be tied to
a material, step, or layer card, it exposes `SelectRecipeCard:<card_id>` so the shell can select the
related detail panel without opening a validation dialog.

Recipe process-step actions also stay inline: duplicate, delete, move up/down, enable, and disable
mutate the in-memory recipe, mark it dirty, and keep the affected step selected. Boundary moves
return structured `blocked` results.

Process-step detail edits use `EditProcessStep:<step_id>:<field>:<value>` action IDs. The workflow
updates typed recipe fields for material, target/stop materials, mask polarity, thickness, notes,
enabled state, and display name, then refreshes dirty/selected-card metadata.

Recipe preview actions are modeless state updates. `PreviewRecipe` records full-recipe preview
scope, and `PreviewRecipeThroughStep:<step_id>` records the selected step and card. Both return a
warning result until a preview backend is connected, rather than opening a blocking solver dialog.

`AttachRecipeToActiveSession` is a modeless bridge from the recipe editor to the session editor.
It requires a saved, clean recipe and an active session document. The controller delegates to the
process-context workflow, then rebuilds the session editor document so recipe status, warnings, and
dashboard fields refresh together.

## Blocking Dialog Policy

Normal setup, capture review, recipe validation, missing artifact handling, and process-context warnings stay modeless. The only normal workflow prompt still allowed is the post-measurement completion choice:

- `Take Another Measurement`
- `Return to Editor`
- `Done`

After `SAVE_EDITS` promotes a pending measurement, `EditorActionResult.post_action_prompt`
contains this exact choice set. The resulting choice is applied through
`MeasurementCompletionChoice`, which either rearms the same parent capture, returns to the parent
capture in the editor, or finishes on the saved measurement.

Pending measurement editor items expose the same modeless review actions as the
`MeasurementWorkflowStateMachine`: save, retake line, discard, and return to the parent capture.

Destructive confirmation, unrecoverable write failure, external overwrite, and catastrophic runtime failures may still use blocking acknowledgement.

## Diagnostics

Advanced Diagnostics surfaces durable state-machine outputs for:

- workflow state
- armed capture primitive
- selected editor item
- selected canvas object
- recipe context
- artifact repair
- mode validation fallback state
- recent failure events

Diagnostics action buttons are rendered from `EditorActionViewModel` rows supplied by the
controller, not hard-coded by the shell. The current action set is Export Diagnostics Bundle,
Copy Command Trace, Open Session Folder, Scan Artifacts, Validate Session, and Validate Modes;
unavailable actions carry disabled reasons when trace events or session paths are missing.

Ephemeral mouse position and window geometry are intentionally not persisted in session JSON and are not required for restore.

## Capture Status Visibility

Armed capture guidance is presented through a shared `CaptureToolStatusViewModel` built from
`SessionRecord.workflow.active_primitive`. The editor status strip and setup guide should consume
that presenter instead of formatting their own gesture text. Unknown durable primitive values become
a modeless navigation-active warning message rather than an exception.

## Known Limitations

- The Qt shell remains minimal and does not yet render polished cards for every state snapshot.
- General point capture remains explicit-unavailable outside the ellipsometry compound child path.
- The post-measurement prompt policy is represented in command/state contracts, but the final Qt
  prompt shell is still a deferred polish item.
