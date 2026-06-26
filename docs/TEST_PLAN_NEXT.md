# Test Plan Next

Last updated: 2026-06-25

Status: historical stabilization test plan with current implementation statuses. Most P0/P1/P2/P3 stabilization tests below now exist under the local names listed in each status block. Current verification evidence is tracked in `docs/IMPLEMENTATION_STATUS.md` and `docs/STABILIZATION_COMPLETION_AUDIT.md`.

## P0.1: Session Lifecycle UI Adapters

Status: implemented in `tests/test_session_lifecycle_commands.py`.

| Test name | Type | Fixture required | Expected behavior | Failure mode prevented |
| --- | --- | --- | --- | --- |
| `test_new_session_menu_uses_folder_label_and_mode_picker` | integration | temp session folder, fake picker | `NEW_SESSION` creates session JSON, sets active document, persists selected mode | menu command remains unavailable or creates wrong mode |
| `test_open_session_menu_loads_selected_session_json` | integration | existing `session.json` fixture | `OPEN_SESSION` loads `SessionDocument`, updates active context, opens editor | user cannot explicitly open saved session |
| `test_open_recent_menu_loads_recent_path` | unit/integration | recent registry with two paths | recent command opens selected session and reorders registry | recent list is transient or ignored |
| `test_save_as_menu_writes_destination_and_updates_loaded_path` | integration | active document, destination folder | Save As writes session JSON and updates active loaded path | save-as writes to old location or returns unavailable |
| `test_path_picker_cancel_is_non_mutating` | unit | fake picker cancel | command result is cancelled/unavailable-by-cancel and active document is unchanged | canceled picker corrupts active state |

Seams protected: `SessionDocument` to Editor, `SessionDocument` to SessionStore, UI emits commands.

## P0.2: Bind Current Layout To Session

Status: implemented in `tests/test_session_lifecycle_commands.py` and `tests/test_klayout_boundary.py`; live installed-KLayout smoke remains opt-in release evidence.

| Test name | Type | Fixture required | Expected behavior | Failure mode prevented |
| --- | --- | --- | --- | --- |
| `test_bind_current_layout_updates_source_layout_context` | unit | fake KLayout layout adapter | active session records path, layout name, top cell, fingerprint, version | source layout remains blank |
| `test_bind_current_layout_restores_canvas_overlays` | integration | session with saved `CanvasObject` records | overlay manager receives restore commands for saved objects | overlays only exist as runtime state |
| `test_bind_current_layout_mismatch_adds_warning` | unit | mismatched fingerprint fixture | session gets structured warning with repair suggestion | silent bind to wrong layout |
| `test_live_klayout_bind_current_layout_smoke` | smoke | real KLayout, synthetic GDS | command binds current view and reports success | adapter works only in fake tests |

Seams protected: CaptureWorkflow to CanvasOverlayManager, SessionDocument to overlays, KLayout adapter boundary.

## P1.1: Production Session Editor Shell

Status: implemented for the unified session editor shell KLayout boundary. Keep broader screenshot testing as release polish.

| Test name | Type | Fixture required | Expected behavior | Failure mode prevented |
| --- | --- | --- | --- | --- |
| `test_qt_session_editor_renders_document_regions` | UI/smoke | simple session fixture | header, navigator, preview, inspector, status render from `SessionDocument` | shell bypasses document view models |
| `test_qt_session_editor_routes_actions_through_command_router` | UI/integration | fake router, action buttons | save/close/repair/process actions route to command IDs | widget mutates state directly |
| `test_qt_session_editor_dirty_close_prompt` | UI/integration | dirty document | close prompts save/discard/cancel and blocks accidental close | dirty edits are lost |
| `test_qt_pending_reviews_render_inside_unified_editor` | UI/integration | pending simple/composite/measurement fixtures | review actions appear in generic editor, not separate mode dialogs | workflow forks into mode-specific UI |

Seams protected: `SessionDocument` to Editor, UI emits commands.

## P1.2: Artifact Generator Handlers

Status: partially implemented for CSV export repair, placeholder SVG generation, measurement
annotation regeneration, overview SVG repair, process-output JSON repair, PowerPoint report-output
repair, no-recipe unavailable repair, live-layout generator requirement routing, and injected live
layout-crop repair. Visual process artifact repair now covers profile and cross-section SVG
generation through role-specific solver/render handlers. No-handler unavailable repair is covered
in artifact repair lifecycle/editor command tests.

| Test name | Type | Fixture required | Expected behavior | Failure mode prevented |
| --- | --- | --- | --- | --- |
| `test_builtin_csv_generator_repairs_stale_export` | integration | stale capture CSV artifact | generator rewrites CSV and marks record present | stale CSV repair action exists but cannot repair |
| `test_builtin_placeholder_generator_writes_visible_svg` | integration | missing placeholder artifact | generator writes SVG and marks record present | placeholder policy has no visible file |
| `test_measurement_annotation_generator_updates_session_artifacts` | integration | saved measurement with missing SVG artifact | generator writes artifact, marks record present, and preserves measurement refs | repair action exists but cannot repair |
| `test_overview_generator_repairs_missing_svg` | integration | session with captures/user labels | overview artifact is written and registered | overview file lacks central record |
| `test_process_output_generator_repairs_pending_solver_artifact` | integration | process session with recipe | generator runs process regeneration, exports JSON, and marks artifact present | process repair action exists but cannot repair |
| `test_process_output_generator_is_unavailable_without_recipe` | unit/integration | process session without recipe | repair request reports recipe requirement | process repair appears runnable without required context |
| `test_profile_render_generator_repairs_visual_process_artifact` | integration | profilometry process session with recipe | profile repair writes an SVG, records render metadata, and marks process output ready | visual process repair only exports JSON metadata |
| `test_profile_render_generator_requires_recipe` | integration | profilometry process session without recipe | profile repair reports recipe requirement before running solver/render | visual process repair bypasses recipe requirements |
| `test_cross_section_artifact_repair_uses_role_specific_renderer` | integration | profilometry process session with recipe | cross-section repair selects the cross-section render profile rather than generic process-output JSON | generic process-output type masks role-specific renderer |
| `test_generated_report_artifacts_have_available_repair_request` | integration | generated report artifact marked stale | repair request is `REBUILD_REPORT` and available | report artifacts are centrally registered but unrebuildable |
| `test_powerpoint_report_repair_rebuilds_missing_deck` | integration | generated PPTX artifact deleted from disk | built-in repair regenerates the deck and preserves report refs | stale/missing report output requires manual workbench export |
| `test_layout_crop_registration_declares_live_layout_requirement` | unit | built-in generator registry | layout crop declares live-layout dependency and is not headless | diagnostics understate crop prerequisites |
| `test_layout_crop_repair_reports_source_layout_requirement_before_handler_gap` | unit/integration | missing layout-crop artifact without source layout | request reports `SOURCE_LAYOUT_REQUIRED_FOR_REPAIR` | UI tells user no handler before required layout binding |
| `test_layout_crop_repair_reports_missing_handler_after_layout_is_bound` | unit/integration | missing layout-crop artifact with source layout | request reports `GENERATOR_HANDLER_UNAVAILABLE` | layout context masks real handler gap |
| `test_layout_crop_repair_exports_live_crop_and_marks_artifact_present` | integration | missing layout-crop artifact with injected crop exporter | exporter receives capture bounds, artifact is written, metadata is updated | live layout crop repair exists only as metadata |
| `test_exporter_uses_active_view_export_image_boundary` | unit/adapter | fake KLayout active-view boundary | KLayout exporter delegates to active view image export and returns file metadata | workflow code imports or simulates KLayout directly |
| `test_injected_layout_crop_repair_service_repairs_selected_crop` | integration | selected layout-crop artifact in editor command path | selected artifact regeneration routes through injected repair service | editor repair bypasses the app-level repair seam |
| `test_repair_request_without_handler_is_unavailable` | unit/integration | missing regenerable artifact with declaration only | request reports `GENERATOR_HANDLER_UNAVAILABLE` | UI shows a dead available repair action |
| `test_cross_section_generator_uses_solver_result_contract` | integration/golden | process session with recipe | generator consumes `SolverResult`/render contract and writes artifact | renderer reads private solver internals |
| `test_generator_failure_creates_stable_warning` | unit | generator that raises | artifact becomes failed with stable warning and repair metadata | exceptions escape or warnings churn |

Seams protected: SessionDocument to Artifacts, SolverResult to RenderProjection, ReportBuilder to ArtifactRegistry.

## P1.3: Reporting Workbench Export Integration

Status: mostly implemented. Destination selection and export-to-selected-folder behavior are
covered in `tests/test_reporting_workbench_output_adapter.py`; KLayout picker wiring is covered in
`tests/test_klayout_session_path_adapter.py`; generated PowerPoint report repair is covered in
`tests/test_report_artifact_repair.py`.

| Test name | Type | Fixture required | Expected behavior | Failure mode prevented |
| --- | --- | --- | --- | --- |
| `test_choose_output_updates_request_and_export_destination` | integration | active document, fake destination picker | outputs are written under selected folder | export path is implicit or unavailable |
| `test_choose_output_cancel_is_non_mutating` | unit | active document, cancelled picker | request output folder remains unchanged | cancelled picker corrupts report request |
| `test_regenerate_stale_uses_injected_repair_service` | integration | stale report artifact, fake repair service | workbench calls `regenerate_stale` and refreshes document | stale outputs are routed through missing-artifact repair |
| `test_stale_outputs_make_regenerate_stale_primary` | unit | stale readiness model | stale readiness makes `regenerate_stale` primary | UI tells operator to regenerate missing artifacts for stale outputs |
| `test_report_output_adapter_selects_folder` | boundary | fake KLayout file dialog | adapter returns selected folder | KLayout picker is not wired |
| `test_reporting_workbench_registers_manifest_artifact` | integration | reportable session fixture | manifest and outputs are central artifacts | report files exist without registry |
| `test_reporting_strict_missing_artifacts_blocks_export` | unit | session with missing required image | strict export blocks with readiness issue | report silently omits required artifact |
| `test_reporting_placeholder_policy_exports_with_warnings` | integration | missing image fixture | placeholder export succeeds with warnings | users cannot export with explicit placeholder policy |

Seams protected: ReportBuilder to ArtifactRegistry, reports consume SessionDocument.

## P1.4: Mode Catalog Alignment

Status: implemented for visible catalog policy in `tests/test_mode_registry.py` and KLayout picker
behavior in `tests/test_klayout_session_path_adapter.py`.

| Test name | Type | Fixture required | Expected behavior | Failure mode prevented |
| --- | --- | --- | --- | --- |
| `test_visible_mode_catalog_hides_legacy_and_internal_modes` | unit | built-in registry | visible modes include only intentional product modes | legacy/internal modes clutter UI |
| `test_new_session_picker_rejects_hidden_legacy_mode_choice` | boundary | fake KLayout picker | hidden legacy mode falls back to simple capture | raw enum values leak into picker |
| `test_fib_cut_mode_is_registered_or_scope_is_absent` | unit/doc | built-in registry/docs | FIB remains descoped until complete mode packet | docs promise missing mode |
| `test_process_flow_summary_policy_is_explicit` | unit | built-in registry | process-flow is either report-only hidden or fully process-aware | ambiguous process mode |
| `test_legacy_cdsem_capture_loads_but_picker_hides_it` | integration | legacy session fixture | loader accepts alias; picker exposes `cdsem_measurement` | duplicate mode confusion |

Seams protected: ModeDefinition to CaptureWorkflow, ModeDefinition to Editor.

## P1.5: Installed External Mode Discovery

Status: implemented for the stabilization contract in `tests/test_mode_registry_config.py` and
`tests/test_klayout_session_path_adapter.py`. External mode IDs are registry/diagnostics-visible,
selectable from KLayout when visible, persisted as open custom session mode IDs when the loaded
registry allows them, and projected into generic editor view models through declared policy.

| Test name | Type | Fixture required | Expected behavior | Failure mode prevented |
| --- | --- | --- | --- | --- |
| `test_load_configured_mode_registry_accumulates_modes_and_warnings` | integration | temp mode JSON folder, missing folder | app registry includes external mode and warning | loader exists but app never uses it |
| `test_bootstrap_diagnostics_reports_external_mode_load_warnings` | integration | registry with external mode and load warning | diagnostics lists external mode and warning | users cannot inspect loaded modes |
| `test_new_session_picker_accepts_registered_external_mode_ids` | boundary | fake KLayout picker, external mode registry | external mode selection returns `SessionModeId` | picker hides configured operator modes |
| `test_registered_external_mode_round_trips_through_session_document` | integration | temp session folder, external mode registry | custom mode ID saves and reopens without fallback warning | external mode sessions cannot be durable |
| `test_registered_external_mode_policy_shapes_editor_view_models` | integration | external mode registry with setup, measurement, dashboard, and metadata policy | editor groups, actions, and fields follow the external mode definition | external modes persist but behave like built-ins or fallbacks |
| `test_unregistered_external_mode_still_falls_back_with_warning` | unit | raw session payload with unknown mode | unknown mode falls back to `simple_capture` with `unsupported_mode` | arbitrary saved IDs bypass validation |
| `test_package_manifest_includes_mode_config_policy` | unit | package manifest | release packaging has documented external mode policy | host install cannot discover modes |

Seams protected: ModeDefinition to setup/capture/editor, diagnostics public state.

## P2.1: Setup Guide Qt Cards

Status: implemented for host-ready card models and KLayout setup-guide shell wiring.

| Test name | Type | Fixture required | Expected behavior | Failure mode prevented |
| --- | --- | --- | --- | --- |
| `test_cards_expose_status_requirement_artifact_and_warning_badges` | unit | setup-guide view model with optional, blocked, and active stages | cards expose status tones, requirement badges, artifact badges, warnings, disabled reasons, and active state | production shell has to infer badge semantics from raw workflow strings |
| `test_factory_renders_setup_stage_cards_into_qt_state` | boundary | fake KLayout Qt widgets | KLayout setup shell records card models and renders setup card labels into Qt regions | Start/Resume Setup keeps using the generic in-memory shell in KLayout |

Seams protected: SetupGuideViewModel to host shell, KLayout UI to setup workflows.

## P2.2: Diagnostics Dashboard

Status: implemented for structured dashboard grouping and required diagnostics rows/actions.

| Test name | Type | Fixture required | Expected behavior | Failure mode prevented |
| --- | --- | --- | --- | --- |
| `test_dashboard_groups_required_rows_and_actions` | integration | active session, session paths, recent command | dashboard exposes grouped session, workflow, artifact, process/report, activity, and action state | production diagnostics remains a flat/debug-only summary |

Seams protected: diagnostics summaries to shell dashboard, actions to command handoffs.

## P2.3: Process Flow Summary Policy

Status: implemented as hidden report-only/load-compatible mode policy.

| Test name | Type | Fixture required | Expected behavior | Failure mode prevented |
| --- | --- | --- | --- | --- |
| `test_process_flow_summary_is_hidden_report_only_compatibility_mode` | unit | built-in mode registry | mode is hidden, report-only, process solver forbidden, and mapped to process-flow reporting | process-flow summary appears as a hollow capture workflow |
| `test_process_flow_summary_policy_is_explicit` | unit | built-in registry/docs | process-flow is either report-only hidden or fully process-aware | ambiguous process mode |

Seams protected: mode catalog to reporting templates, hidden compatibility modes to picker policy.

## P2.4: Dense Overview Visual Regression

Status: implemented with a synthetic testchip label-stress golden summary.

| Test name | Type | Fixture required | Expected behavior | Failure mode prevented |
| --- | --- | --- | --- | --- |
| `test_dense_real_layout_overview_matches_golden_summary` | golden/integration | `process_planner_testchip.geometry.json` `label_stress_test` shapes | overview extracts 18 targets, places 15 labels, routes 15 leaders, omits low-priority labels, resolves collisions, and renders matching SVG element counts | dense CAD-like label routing regresses without obvious unit failures |

Seams protected: overview extraction to layout planner, leader router to SVG renderer, synthetic layout fixture to reportable overview artifact behavior.

## P2.5: Legacy CDSEM Alias Deprecation

Status: implemented through visible catalog policy and legacy alias compatibility tests.

| Test name | Type | Fixture required | Expected behavior | Failure mode prevented |
| --- | --- | --- | --- | --- |
| `test_visible_mode_catalog_hides_legacy_and_internal_modes` | unit | built-in registry | `cdsem_capture` is hidden and `cdsem_measurement` remains visible | duplicate CDSEM operator modes appear in picker |
| `test_legacy_cdsem_capture_mode_remains_registered` | unit | built-in registry | old `cdsem_capture` sessions still resolve to a valid mode definition | saved legacy sessions become unsupported |

Seams protected: mode picker to `ModeRegistry.visible_mode_ids()`, legacy saved session IDs to mode registry compatibility.

## P2.6: Recipe Picker/Open-File Shell

Status: implemented through recipe path adapter contracts, app command routing, setup attach routing, and KLayout picker adapter coverage.

| Test name | Type | Fixture required | Expected behavior | Failure mode prevented |
| --- | --- | --- | --- | --- |
| `test_open_recipe_command_uses_adapter_selected_path` | integration | temp recipe JSON, fake recipe path adapter | app command opens selected recipe and records `metadata.recipe_path` | menu command opens editor only or requires hidden payload state |
| `test_open_recipe_cancel_is_non_mutating` | integration | fake cancelling recipe path adapter | cancelled picker does not mutate current recipe | cancel corrupts recipe editor state |
| `test_save_recipe_as_command_uses_adapter_destination` | integration | dirty in-memory recipe, fake destination picker | app command saves JSON, clears dirty state, and reports output path | Save As remains unavailable without manually encoded action payload |
| `test_setup_attach_recipe_command_uses_adapter_selected_path` | integration | process-aware setup session, fake attach picker | setup command attaches selected recipe to canonical process context | setup guide recipe attachment remains a dead command |
| `test_recipe_path_adapter_selects_open_save_and_attach_paths` | boundary | fake KLayout file dialog | KLayout adapter returns selected open, save-as, and attach recipe paths | production KLayout shell lacks recipe file picker wiring |

Seams protected: UI command to recipe path adapter, recipe editor controller to recipe store, setup guide to process context attachment.

## P3.1: Standalone Point Capture Product Workflow

Status: implemented through standalone point pending-capture commit, KLayout gesture adapter routing, and pending review promotion coverage.

| Test name | Type | Fixture required | Expected behavior | Failure mode prevented |
| --- | --- | --- | --- | --- |
| `test_point_capture_creates_standalone_pending_capture` | unit | clean session, `PointCaptureTool` | Shift-click creates one pending point capture with canonical point geometry | generic point capture remains a handled no-op |
| `test_point_click_can_save_as_standalone_capture` | integration | pending point capture | pending review promotes point geometry into a saved capture and saved canvas object | point captures cannot become durable session records |
| `test_point_capture_uses_next_pending_id_after_saved_capture` | unit | saved point capture | second point capture uses the next pending id | pending ids collide after saved point captures |
| `test_klayout_point_capture_commits_standalone_pending_capture` | boundary | fake KLayout gesture adapter | KLayout Shift-click updates session and restores overlays | production boundary reports unavailable or skips overlay refresh |

Seams protected: KLayout gesture adapter to `PointCaptureTool`, point tool to pending capture state, pending review to saved point geometry.

## P3.2: Standalone Line Capture Product Workflow

Status: implemented through parentless line pending-capture commit, KLayout gesture adapter routing, and pending review promotion coverage.

| Test name | Type | Fixture required | Expected behavior | Failure mode prevented |
| --- | --- | --- | --- | --- |
| `test_line_drag_can_save_as_standalone_capture` | integration | parentless `LineCaptureTool` drag | pending review promotes line geometry into a saved capture and saved canvas object | generic line capture only works as a child measurement/profile primitive |
| `test_line_capture_uses_next_pending_id_after_saved_capture` | unit | saved standalone line capture | second line capture uses the next pending id | pending ids collide after saved line captures |
| `test_klayout_line_capture_commits_standalone_pending_capture` | boundary | fake KLayout gesture adapter | parentless KLayout Shift-drag creates a pending line capture and restores overlays | production boundary drops parentless line gestures |

Seams protected: KLayout gesture adapter to `LineCaptureTool`, line release routing to standalone pending capture state, pending review to saved line geometry.

## P3.3: Broader Live KLayout GUI Gesture Automation

Status: implemented through opt-in GUI probes and batch `pya` capture-adapter probes. Pure tests skip
the installed-KLayout lanes unless `MPP_RUN_KLAYOUT_TESTS=1` or `MPP_RUN_KLAYOUT_UI_TESTS=1` is set.

| Test name | Type | Fixture required | Expected behavior | Failure mode prevented |
| --- | --- | --- | --- | --- |
| `test_klayout_standalone_point_capture_adapter_does_not_mutate_layout` | smoke | real KLayout batch runtime, synthetic layout | standalone Shift-click creates pending point geometry, restores overlay commands, and leaves source layout shapes unchanged | standalone point works only in pure/fake boundary tests |
| `test_klayout_standalone_line_capture_adapter_does_not_mutate_layout` | smoke | real KLayout batch runtime, synthetic layout | standalone Shift-drag creates pending line geometry, restores overlay commands, and leaves source layout shapes unchanged | standalone line works only in pure/fake boundary tests |
| `test_klayout_line_capture_adapter_does_not_mutate_layout` | smoke | real KLayout batch runtime, synthetic layout | measurement Shift-drag still creates a child measurement without mutating source layout | standalone line routing regresses parented measurement gestures |
| `test_klayout_profilometry_line_capture_adapter_does_not_mutate_layout` | smoke | real KLayout batch runtime, synthetic layout | profilometry child-line capture still routes through mode policy and overlays | generic line routing drops process-aware child features |
| `test_klayout_ellipsometry_point_capture_adapter_does_not_mutate_layout` | smoke | real KLayout batch runtime, synthetic layout | ellipsometry child-point capture still routes through mode policy and overlays | standalone point routing regresses process-aware child points |

Seams protected: installed KLayout runtime to gesture adapter, gesture adapter to shared capture tools, overlay restore boundary to read-only source layouts.

## P3.4: Process Solver Physics Expansion

Status: resolved for stabilization through executable accuracy-envelope fixtures and etch
depth/blocker diagnostics. Calibrated physics and independent backend comparison remain future scope.

| Test name | Type | Fixture required | Expected behavior | Failure mode prevented |
| --- | --- | --- | --- | --- |
| `test_directional_etch_reports_exhausted_target_material` | unit | sampled oxide stack with stop layer | solver emits `ETCH_TARGET_EXHAUSTED` when requested etch depth exceeds available target material | excessive etch requests silently look physically complete |
| `test_directional_etch_with_blocker` | unit | non-target blocker over target material | solver preserves blocked target material and emits `ETCH_BLOCKED_BY_NON_TARGET` | target etch appears to do nothing without an actionable reason |
| `test_all_required_golden_recipes_exist_and_validate` | golden/metadata | synthetic recipe fixtures | each solver fixture declares an accuracy envelope with model, claim, coverage, and exclusions | qualitative fixtures drift into unstated calibrated-physics claims |

Seams protected: operation executors to sampled geometry kernel, solver diagnostics to frames/results, solver fixture metadata to product claims.

## Cross-Cutting Gates

Run after each P0/P1 packet:

- `python -m pytest tests/integration/dependency/test_dependency_direction.py`
- `python -m tools.quality_gates`
- targeted tests for changed subsystem
- `python -m tools.release_check --include-klayout` before declaring shippable stabilization
