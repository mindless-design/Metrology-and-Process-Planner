# No Bypass Audit

Last updated: 2026-06-25

## Checklist

| Bypass class | Status | Evidence / notes |
| --- | --- | --- |
| Direct JSON writes outside session stores | No core bypass found | Session JSON writes are through `SessionJsonStore`, document writer, or test fixtures. Recipe/process-output stores write their own derived JSON, not session state. |
| Raw `open/write` for `session.json` | No product bypass found | Persistence code owns file IO; tests and fixture generators write fixtures. |
| UI callbacks mutating raw session dicts | No bypass found | UI shells route action IDs; app controllers and workflow dispatchers return typed results/documents. |
| UI callbacks creating artifacts directly | No bypass found | Artifact creation flows through render bridge, artifact generators, reporting services, or process-output store. |
| Mode-specific capture handlers | No critical bypass found | Built-ins define declarative policies; shared compound/canvas workflows implement behavior. |
| Mode-specific editor windows | No bypass found for capture/measurement | Unified editor and generic review adapters are used. Recipe editor is a separate product surface, not mode-specific capture UI. |
| Mode-specific report builders | No bypass found | Reporting uses policy/section services and report models. |
| Raw filenames stored in captures | Guarded | Captures store `artifact_refs`; central `ArtifactRecord.relative_path` owns paths. Legacy conversion is migration-only. |
| Measurements stored globally without owner | No bypass found | Measurements are nested under captures. |
| Solver called directly from UI | No bypass found | App/editor actions route through process-regeneration workflows/services. |
| Renderer called directly from UI | No bypass found | Rendering is behind render bridge/report/overview services. |
| Artifact repair bypassing repair service | No bypass found | Repair metadata/request generation is centralized in artifact workflows. |
| Workflow importing app layer | Found and fixed | `recipe_editor_*` workflow modules now import `domains.commands` instead of `app.command_types`/`app.commands`. |

## Intentional Exceptions

- Tests and fixture generators may write JSON/CSV directly to create controlled inputs.
- `persistence.recipe_store` and `persistence.process_output_store` write derived recipe/output
  JSON, not canonical session documents.
- `app.command_types` re-exports `domains.commands.CommandId` for backward compatibility; the
  owner of the enum is now the domain command contract.

## Follow-Up

Keep `tests/integration/dependency/test_dependency_direction.py` and import-linter in release
checks. Add a future IO audit test only if direct session writes start to reappear outside
persistence/document lifecycle modules.
