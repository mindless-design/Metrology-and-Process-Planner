# Artifact and Reporting Audit

Last updated: 2026-06-25

## Artifact Registry

The artifact registry is implemented as a first-class `artifacts` map in session JSON. Local `artifact_refs` on captures, measurements, reports, and process outputs point back to central `ArtifactRecord` ids.

Supported statuses match the requested lifecycle vocabulary: `present`, `missing`, `stale`, `failed`, `placeholder`, `external`, `pending`, `pending_solver`, `superseded`, and `intentionally_ignored`.

## Artifact Lifecycle

| Capability | Status | Notes |
| --- | --- | --- |
| central artifact registry | implemented | `ArtifactRecord` persisted in `SessionRecord.artifacts` |
| local artifact refs | implemented | captures/measurements/process outputs/reports use refs |
| artifact statuses | implemented | enum covers requested statuses |
| dependencies and signatures | implemented | stale scanner compares dependency signatures |
| artifact scanner | implemented | missing/stale/failed warnings |
| artifact repair service | implemented | single and bulk repairs |
| generator registry | mostly_implemented | high-value handlers exist for CSV, placeholders, annotations, overviews, process-output JSON, PowerPoint report outputs, injected live layout crop repair, and visual process SVG repair |
| placeholder artifacts | implemented | placeholders/warnings and repair metadata |
| stale artifact detection | implemented | dependency signature based |
| missing artifact warnings | implemented | structured warning records |
| CSV/report stale tracking | implemented | CSV/report stale codes |

## Artifact Type Coverage

| Type | Status | Notes |
| --- | --- | --- |
| site_image/reference_image | partially_implemented | registry roles exist; live layout crop repair is available when a live KLayout exporter is injected |
| annotated_site_image | partially_implemented | annotation pipeline exists; generator breadth varies |
| measurement_detail_image | implemented | pending/repairable annotation artifacts |
| line_annotation_image | implemented | compound placeholders and annotation roles |
| point_annotation_image | implemented | ellipsometry placeholders |
| overview_image | implemented | overview SVG artifact generation |
| profile_image | implemented | profile repair writes solver/render SVG artifacts |
| cross_section_image | implemented | renderer pipeline and repair generator exist |
| stack_image | implemented | point-stack role has a role-specific visual process repair generator |
| full_stack_compressed_image | implemented | render profile exists |
| process_flow_frame | implemented | render profile and repair generator exist |
| csv_export | implemented | exporter and artifact registration path |
| powerpoint_deck | implemented | PPTX backend exists |
| PDF export | implemented | PDF backend exists |
| image bundle export | implemented | image package backend exists |
| report_manifest | implemented | manifest builder/exporter |
| debug_trace | implemented | diagnostics bundle/action support |

## Metadata Export

CSV export includes session id/name/mode, capture id/sequence/status, coordinate mode, units, box bounds, center, width, height, source layout path/file/top cell, first line/point feature coordinates, measurement start/end/length/specs, artifact paths/statuses, warning count, notes, and tags. This is enough to locate captured boxes, line features, point features, and measurements in CAD coordinates when the session source layout context is populated.

Remaining gaps are UI affordances for copy-coordinate actions and ensuring source layout binding is populated by the live KLayout adapter.

## Reporting

Reporting is implemented as a headless service over `SessionDocument`. It builds `ReportDocument` models, assesses readiness, exports through PPTX/PDF/CSV/image backends, and writes a manifest. The KLayout-integrated reporting workbench exists as a modeless controller/shell and opens only when an active editor document and paths are available.

Templates include capture catalog, metrology report, CAD review report, process review report, FIB planning package, process flow summary, debug artifact report, plus engineering/measurement/executive variants.

## Critical Question

Can reports be generated from saved session JSON and artifacts without relying on live UI state?

Answer: implemented for the service/core path. The report service consumes a `SessionDocument` loaded from session JSON and artifact files. Live UI state is not required for report model generation, and generated PowerPoint report artifacts can be repaired from saved `ReportRecord` metadata. Operator export UX still needs production polish.

## Recommended Actions

1. Broaden non-PPTX report/output repair only where those formats become operator-critical.
2. Polish production file/destination picker UX for reporting exports.
3. Ensure live layout binding fills `source_layout` so exported CAD metadata is complete.
4. Add report readiness UI that clearly groups missing/stale/placeholder artifacts and repair actions.
