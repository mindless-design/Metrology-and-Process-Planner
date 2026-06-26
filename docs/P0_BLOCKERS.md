# P0 Blockers

Last updated: 2026-06-25

P0 means the plugin cannot reliably function as a document-based workflow tool until the issue is fixed. The original audit identified two P0 blockers. Both now have implemented command paths and pure/fakeable tests; live installed-KLayout smoke remains opt-in verification rather than an unresolved command-path blocker. The 2026-06-25 completion pass ran `python -m tools.release_check --include-klayout` successfully.

## Resolved P0.1: Session Lifecycle UI Adapters

Title: Menu/start-screen New/Open/Open Recent/Save As collect required path and mode inputs.

Resolution: `SessionDocumentCommandService` now uses the fakeable `SessionPathAdapter` contract for new/open/recent/save-as inputs. KLayout plugin registration supplies `KLayoutSessionPathAdapter`, while pure tests inject fake picker selections.

Affected systems:

- KLayout menu
- Session editor start screen
- `SessionDocument` lifecycle
- Active session context
- Recent sessions
- Reporting and artifact workflows that depend on an active loaded document

Evidence:

- New Session creates `session.json`, opens the editor, and sets the active document.
- Open Session opens selected `session.json`.
- Open Recent uses `RecentSessionRegistry`.
- Save As writes the selected destination and updates `loaded_path`.
- Canceled picker results do not mutate active document state.

Files/modules likely involved:

- `python/metrology_process_planner/app/session_document_commands.py`
- `python/metrology_process_planner/app/session_editor_lifecycle.py`
- `python/metrology_process_planner/app/session_editor_surface.py`
- `python/metrology_process_planner/app/session_editor.py`
- `python/metrology_process_planner/ui/session_editor/*`
- `python/metrology_process_planner/infrastructure/klayout/plugin.py`
- `python/metrology_process_planner/app/command_catalog.py`

Tests:

- `test_new_session_menu_uses_folder_and_mode_picker`
- `test_open_session_menu_loads_selected_session_json`
- `test_open_recent_menu_loads_registry_path`
- `test_save_as_menu_writes_selected_destination`
- `test_path_picker_cancel_returns_cancelled_route_result`

Acceptance criteria:

- New Session creates `session.json` and standard folders.
- Open Session opens an explicit existing `session.json`.
- Open Recent uses the recent registry and updates active editor state.
- Save As writes to a selected destination and updates `loaded_path`.
- No normal supplied-input path returns `unavailable`.
- Canceled dialogs do not mutate active document state.

Residual risk: live dialogs are covered through the KLayout adapter boundary, while full GUI interaction remains part of the opt-in KLayout UI lane, which passed in the latest release check.

## Resolved P0.2: Bind Current Layout To Session

Title: The active live KLayout view can be bound through a host adapter.

Resolution: `BIND_CURRENT_LAYOUT_TO_SESSION` now uses a fakeable `SessionLayoutAdapter`, persists `SourceLayoutContext`, emits structured mismatch warnings, and replays durable canvas overlays through an injected overlay manager. KLayout plugin registration supplies `KLayoutSessionLayoutAdapter` and `KLayoutOverlayBackend`.

Affected systems:

- `SourceLayoutContext`
- coordinate context
- canvas overlays
- metadata export
- layout crop and overview artifact generation
- diagnostics
- KLayout UI automation

Evidence:

- Binding updates source layout path, layout name, top cell, fingerprint, and KLayout version.
- The updated context is saved to `session.json`.
- Mismatched previous/current layout metadata creates `SOURCE_LAYOUT_MISMATCH`.
- Saved canvas overlays are restored through `CanvasOverlayManager`.
- KLayout adapter extraction is tested with a fake `pya` boundary object.

Files/modules likely involved:

- `python/metrology_process_planner/app/session_document_commands.py`
- `python/metrology_process_planner/domains/session/canonical.py`
- `python/metrology_process_planner/infrastructure/klayout/geometry.py`
- `python/metrology_process_planner/infrastructure/klayout/overlays.py`
- `python/metrology_process_planner/workflows/overlays.py`
- `python/metrology_process_planner/app/diagnostics_summary.py`

Tests:

- `test_bind_current_layout_updates_source_layout_context`
- `test_bind_current_layout_restores_saved_canvas_overlays`
- `test_bind_current_layout_mismatch_adds_warning`
- live KLayout smoke for binding current layout and restoring overlays

Acceptance criteria:

- Binding records source layout fields on the active session.
- Overlay restore uses saved `CanvasObject` records only.
- Layout mismatch creates a structured warning with repair suggestion.
- Diagnostics shows bound layout and overlay restore status.
- The KLayout layout database is not mutated by overlay restore.

Residual risk: keep the live installed-KLayout bind smoke in the opt-in release lane for future packaging runs.
