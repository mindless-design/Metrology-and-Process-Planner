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

## Blocking Dialog Policy

Normal setup, capture review, recipe validation, missing artifact handling, and process-context warnings stay modeless. The only normal workflow prompt still allowed is the post-measurement completion choice:

- `Take Another Measurement`
- `Return to Editor`
- `Done`

Destructive confirmation, unrecoverable write failure, external overwrite, and catastrophic runtime failures may still use blocking acknowledgement.

## Diagnostics

Advanced Diagnostics surfaces durable state-machine outputs for:

- workflow state
- armed capture primitive
- recipe context
- artifact repair

Ephemeral mouse position and window geometry are intentionally not persisted in session JSON and are not required for restore.

## Known Limitations

- The Qt shell remains minimal and does not yet render polished cards for every state snapshot.
- General point capture remains explicit-unavailable outside the ellipsometry compound child path.
- The post-measurement blocking prompt policy is represented in command/state contracts, but the final Qt prompt shell is still a deferred polish item.
