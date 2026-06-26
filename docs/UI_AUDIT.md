# UI Audit

Last updated: 2026-06-25

## Menu and Launcher

| Entry | Command | Opens | State required | No active session | Active session | Duplicated elsewhere | Status |
| --- | --- | --- | --- | --- | --- | --- | --- |
| Start / Resume Measurement Setup | `OPEN_SETUP_GUIDE` | Setup Guide | none, but useful with active session | opens unavailable/no-session guide | opens/raises KLayout-backed setup card shell | editor reopen setup | implemented |
| Session Editor | `OPEN_SESSION_EDITOR` | Session Editor/start screen | none | opens start screen | opens/raises active document | editor header | implemented |
| Open Session... | `OPEN_SESSION` | intended editor document | session path needed | unavailable | unavailable/path needed | start screen action | partially_implemented |
| New Session... | `NEW_SESSION` | intended new editor document | output folder/mode needed | unavailable | unavailable/path needed | start screen action | partially_implemented |
| Edit Recipe | `OPEN_RECIPE_EDITOR` | Recipe Editor | none | opens current recipe surface; open/save-as commands use adapter pickers | opens current recipe surface; attach uses active session bridge | editor process actions | implemented |
| End Active Session | `END_ACTIVE_SESSION` | closes modeless session surfaces | clean/no pending or dirty | succeeds/no-op | blocks dirty/pending or closes | editor close | implemented |
| Advanced Diagnostics | `OPEN_DIAGNOSTICS` | Diagnostics panel | active session | unavailable | opens grouped dashboard/action shell | diagnostics actions | implemented |
| Reporting Workbench | `OPEN_REPORTING_WORKBENCH` | Reporting Workbench | active editor doc and paths | unavailable | opens workbench | Build Report action | partially_implemented |

Normal menu clutter is acceptable: it has eight primary entries. Workflow commands are command metadata but not top-level menu items.

## Session Editor Structure

The generic shell has the requested major regions: header/session bar, primary actions, left navigator, center preview, right inspector/actions, and bottom status. The implementation is an injectable/fakeable widget shell rather than a polished Qt surface.

| Capability | Status | Notes |
| --- | --- | --- |
| Dashboard | implemented | document builder creates dashboard item and summary view models |
| Setup status | implemented | header/status and setup group use setup state |
| Pending capture review | implemented | pending items and save/retake/discard actions |
| Pending composite review | implemented | save composite, retake child/parent, discard, exit actions |
| Pending measurement review | implemented | nested pending measurements and save/retake/discard |
| Saved capture inspection | implemented | navigator and metadata adapters |
| Measurement inspection | implemented | nested item and artifact refs |
| Grid dataset inspection | partially_implemented | model/group exists; UX depth is thin |
| Process output inspection | implemented | first-class items and regenerate action |
| Artifact inspection | implemented | artifact health/details and repair actions |
| Warning inspection | implemented | warning rows/actions |
| Report/export inspection | partially_implemented | reporting workbench modeless surface exists |
| Metadata editing | partially_implemented | dirty metadata edits apply through save; final widgets pending |
| Dirty-state tracking | implemented | `DirtyState`, save/discard/close blockers |
| Artifact repair actions | implemented | selected and bulk actions |
| Process context actions | implemented | attach/detach/validate/regenerate |
| Report actions | partially_implemented | workbench opens with active document |

## View-Model Separation

Widgets consume `SessionDocument`, navigator rows, preview rows, metadata rows, `EditorAction`, setup view models, diagnostics rows, and report workbench view models. The audited shell code does not read raw session JSON directly; loading and preserving raw payload belongs to the store.

## Setup Guide

The setup guide is modeless through `WindowRegistry` and `ModelessSurfaceShell`. It renders stage cards from mode/session state and routes stage actions through `CommandRouter`. KLayout registration injects a setup-guide-specific surface factory that renders status, requirement, artifact, warning, action, disabled, and active-stage card metadata. It supports no-session state without prompt storms.

Stage support is implemented for coordinate origin, origin point/reference, optical alignment, SEM alignment, recipe validation, optional skip, and ready-for-capture style actions. Recipe validation is blocked for non-process setup.

## Capture Tools UI

Gesture hints are correct:

- box: Left Shift + drag box
- line/measurement: Left Shift + drag line
- point/ellipsometry point: Left Shift + click point
- cancel: command path disarms capture and clears live preview

Point capture now supports both standalone pending point captures and compound ellipsometry child points.

## UI Risks

1. Production Qt shells still need live visual QA compared with the core view models.
2. File picker and destination picker inputs are missing for top-level document commands.
3. Live KLayout layout binding is missing for source layout rebinding and delayed overlay restoration.
4. Some actions rely on typed path handoffs rather than launching platform behavior.

## Recommended Actions

1. Build the Qt start screen/file picker around existing lifecycle methods.
2. Implement `Bind Current Layout to Session`.
3. Render remaining editor/reporting view models in production Qt widgets.
4. Add UI adapter tests for every currently unavailable path/layout command.
