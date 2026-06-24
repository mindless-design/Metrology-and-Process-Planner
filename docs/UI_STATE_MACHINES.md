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

Setup guide stage actions are emitted as command IDs by the pure presenter and routed by the
`SetupGuideController` through the shared `CommandRouter`. Setup capture commands arm shared
canvas primitives and update durable `WorkflowState`; setup configuration commands update
canonical setup fields. Deferred setup commands should return structured unavailable results; they
should not become widget-local logic or blocking prompts.

Disabled editor actions carry `disabled_reason` in the same view model as their command ID. UI
shells should render disabled actions with that reason, and dispatch should return the same reason
as a structured `unavailable` result rather than silently doing nothing.

Recipe editor card/header actions use `RecipeEditorActionDispatcher` before any widget-specific
behavior. The dispatcher converts action IDs such as `AddProcessStep:directional_etch` to typed
commands, applies safe in-memory recipe edits, and returns structured unavailable results for
deferred save/open/attach workflows. The modeless recipe editor shell exposes a generic action
callback; widgets should call that callback rather than mutating recipe state directly. Closing the
recipe editor is a controller/window-registry action, not a recipe mutation.

Recipe editor selection should render through `selected_detail` on `RecipeEditorViewModel`.
Material, process-step, and layer cards expose their own field/action models there, keeping card
selection and detail editing on the same modeless view-model spine.

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
