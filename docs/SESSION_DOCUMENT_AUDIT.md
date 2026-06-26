# Session Document Audit

Last updated: 2026-06-25

## Summary

Session JSON is the canonical product document. The current schema is document-centered and includes the top-level blocks requested for durable workflow state: `schema`, `session`, `paths`, `source_layout`, `coordinates`, `setup`, `captures`, `grid_datasets`, `process_context`, `process_outputs`, `reports`, `artifacts`, `warnings`, `workflow`, `extensions`, and `audit`.

The main gap is not persistence itself. It is the production UI path into persistence: top-level menu commands that need file/folder/layout input return structured unavailable results until a Qt/KLayout adapter supplies that input.

## Top-Level Blocks

| Block | Status | Notes |
| --- | --- | --- |
| `schema` | implemented | versioned `SchemaRecord`; current canonical version is checked on load/save |
| `session` | implemented | id, name, mode, created/updated timestamps |
| `paths` | implemented | relative path policy and standard folders |
| `source_layout` | partially_implemented | record exists; live binding command is not wired |
| `coordinates` | implemented | units, axis, origin, scale |
| `setup` | implemented | setup guide reads/writes durable state |
| `captures` | implemented | saved captures with geometry, metadata, children, measurements |
| `grid_datasets` | partially_implemented | record support exists; UX depth thinner |
| `process_context` | implemented | active recipe/context state and validation warnings |
| `process_outputs` | implemented | solver summaries and process output records |
| `reports` | implemented | report records and report artifacts |
| `artifacts` | implemented | central artifact registry |
| `warnings` | implemented | structured warning records |
| `workflow` | implemented | resume/active/pending workflow state |
| `extensions` | implemented | canvas objects and pending captures live here in v5 |
| `audit` | implemented | migration/audit events |

## Lifecycle

| Flow | Status | Evidence | Gap |
| --- | --- | --- | --- |
| create new session | partially_implemented | `SessionStore.new_session`, `NewSessionRequest`, `SessionEditorLifecycleMixin.new_session` | menu/file picker/mode picker wiring |
| open existing session JSON | partially_implemented | `SessionDocumentLoader.load`, `open_session_path`, `SessionStore.open_session` | `OPEN_SESSION` menu command lacks path picker |
| open recent | partially_implemented | `RecentSessionRegistry` exists | no persisted host recent list or menu callback |
| save session | implemented | `SessionDocumentWriter.save`, atomic temp/backup replace | production UI save feedback |
| save as | partially_implemented | `save_current_session_as(destination)` | menu command needs destination picker |
| close session | implemented | dirty blocker and clear active context | final dirty prompt UI |
| dirty-state prompt | partially_implemented | close returns blocked unless save/discard/cancel | prompt rendering deferred to UI |
| active session context | implemented | `ActiveSessionContext.from_document` | n/a |
| source layout binding | partially_implemented | `SourceLayoutContext` and warnings exist | `Bind Current Layout to Session` not wired |
| session folder structure | implemented | `SessionPaths` creates artifacts/exports/images/drawings/reports/process_outputs | n/a |

## Critical Question

Can a user explicitly open a `session.json` and edit that session?

Answer: partially_implemented. The core supports it through `SessionEditorController.open_session_path(...)` and `SessionStore.open_session(...)`, and the editor can load/edit/save the document. The top-level KLayout `Open Session...` command does not yet collect a path, so the operator-facing flow is incomplete.

## Canonical State Rule

Every saved feature should have a durable JSON record. Current findings:

- saved captures: durable `captures[]`
- pending captures: durable `extensions.canvas.pending_captures`
- overlays: durable `CanvasObject` proxies in `extensions.canvas.canvas_objects`, not canonical UI state
- measurements: durable nested `MeasurementRecord`
- compound line/point features: durable capture geometry feature payloads/extensions
- artifacts: central `artifacts` map plus local refs
- process context: durable `process_context` plus capture/process extensions
- process outputs: durable `process_outputs[]`
- reports: durable `reports[]` and report artifacts
- diagnostics events: runtime sink/export bundle, not canonical session history except explicit warnings/audit

No feature should be added as only a UI object, CSV row, or image file. The existing architecture supports that rule.

## Schema and Migration

Legacy integer-schema payloads are migrated through `SessionRecord.from_dict(...)`. v5 payloads preserve unknown top-level fields on editor save via `merged_payload(...)`. Unsupported future schema versions produce warnings/errors rather than silent corruption.

## Recommended Actions

1. Wire `OPEN_SESSION`, `NEW_SESSION`, `OPEN_RECENT_SESSION`, and `SAVE_SESSION_AS` to real Qt path/mode/destination selection.
2. Implement `BIND_CURRENT_LAYOUT_TO_SESSION`.
3. Persist recent sessions outside the transient registry if operator workflow requires cross-run history.
4. Keep schema validation and unknown-field preservation in all future document edits.
