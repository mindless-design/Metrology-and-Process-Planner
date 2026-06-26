# Image Pipeline and Image-Driven UI Quality Audit

Date: 2026-06-25

## Canonical Contracts

- Capture geometry and feature truth lives on `CaptureRecord.geometry` and is mapped by `python/metrology_process_planner/rendering/coordinates.py`.
- Capture visual artifacts are generated through `python/metrology_process_planner/workflows/artifacts/visual_capture_generator.py`, with shared support in `visual_capture_support.py` and SVG emission in `visual_capture_svg.py`.
- Annotation scenes are backend-independent `DrawingScene` records from `python/metrology_process_planner/rendering/annotation_planner.py`, rendered by `python/metrology_process_planner/rendering/svg_renderer.py`.
- Artifact identity, status, repair action, file metadata, and source linkage remain in canonical `ArtifactRecord` fields/extensions under the session artifact registry.
- Report image consumption is renderer-neutral through `python/metrology_process_planner/reporting/models.py`, `gallery.py`, `overview.py`, `image_backend.py`, and `pptx_backend.py`.
- UI preview state is adapter-driven through `python/metrology_process_planner/ui/preview_widgets/presenter.py` and placeholder text in `workflows/editor/preview_placeholders.py`.

## Image-Producing Paths Found

- Raw site fixture image: `tools/generate_visual_quality_gallery.py` writes `tests/output/visual_review_gallery/images/cap-001.png`.
- Labeled capture image: `generate_labeled_site_artifact()` writes `images/<capture>-site_image_labeled.svg`.
- Site overview image: `generate_site_overview_artifact()` writes `images/<capture>-site_overview_image.svg`.
- Line, point, and measurement annotation images: `generate_annotation_artifact()` writes shared `DrawingScene` SVGs.
- Cross-section/process images: `tools/generate_visual_quality_gallery.py` drives `SvgCrossSectionRenderer` over process fixtures and writes `tests/output/visual_review_gallery/process/*.svg`.
- Report image bundle: `ImagePackageBackend` packages present image artifacts and placeholder manifests for missing image artifacts.

## Display and Report Surfaces

- Session/review previews consume `PreviewModel` values from `PreviewPresenter`.
- Reporting gallery figures are built by `reporting/gallery.py`; overview report sections use `reporting/overview.py`.
- PPTX export places figures through `reporting/pptx_images.py` and captions through `reporting/formatting.py`.
- Portable image export uses `reporting/image_backend.py`, preserving missing-image placeholders instead of failing silently.
- Visual QA gallery uses `tools/generate_visual_quality_gallery.py` and `python/metrology_process_planner/testing/visual_quality.py`.
- Rendered visual evidence is repeatable through `tools/render_visual_quality_previews.py`.

## Visual Findings

Generated and inspected:

- `tests/output/visual_review_gallery/images/cap-001.png`
- `tests/output/visual_review_gallery/rendered_previews/images__cap-001-line_annotation_image.svg.png`
- `tests/output/visual_review_gallery/rendered_previews/images__cap-001-measurement_annotation_image.svg.png`
- `tests/output/visual_review_gallery/rendered_previews/images__cap-001-point_annotation_image.svg.png`
- `tests/output/visual_review_gallery/rendered_previews/images__cap-001-site_image_labeled.svg.png`
- `tests/output/visual_review_gallery/rendered_previews/images__cap-001-site_overview_image.svg.png`
- `tests/output/visual_review_gallery/rendered_previews/process__*.svg.png`
- `tests/output/visual_review_gallery/rendered_previews/contact_sheet.png`
- `tests/output/report_visual_evidence/report_page_1.png`
- `tests/output/report_visual_evidence/report_page_5_artifact_gallery.png`

Problems found and fixed:

- Capture SVGs referenced source images in a way that did not survive Qt/headless SVG rendering. Fixed by embedding the source raster as a data URI while recording `source_image_artifact_id`, `source_image_relative_path`, and `source_image_embedding` on the generated artifact.
- Qt headless SVG rendering produced unreadable block glyphs for SVG text. Fixed by emitting rasterized text image fallbacks plus hidden SVG text for structural inspection.
- Point annotation labels near the image edge could clip. Fixed by clamping point-label positions inside the canvas.
- Annotation labels were low contrast over source imagery. Fixed by adding a dark stroke to rasterized label text.
- The gallery had a nested `images/images/cap-001.png` workaround that hid bad SVG image references. Removed it and added missing-reference checks.

## Coverage Gaps Closed

- Added `tests/test_image_pipeline_quality.py` for capture image embedding, edge-label placement, missing SVG image references, source-artifact metadata linkage, UI preview placeholder behavior, report image bundle consumption, and gallery manifest contracts.
- Expanded visual QA behavior in `python/metrology_process_planner/testing/visual_quality.py` to catch missing local SVG image references.
- Added `tools/render_visual_quality_previews.py` to render gallery SVGs through Qt and write `tests/output/visual_review_gallery/rendered_previews/contact_sheet.png`.
- Existing focused suites now exercise annotation export, editor render bridge behavior, overview diagrams, cross-section rendering, report pipeline, and report visual formatting.
- Rendered PDF evidence through `pypdfium2` confirmed report pages are nonblank/readable and missing artifact gallery figures remain visible as captions/placeholders.

## Remaining Gaps

- Full installed-KLayout UI screenshot automation was not run in this pass; verification used Qt SVG rendering through PyQt plus model-level UI preview tests.
- PPTX was verified structurally through media relationships, slide bounds, and placeholder XML tests; a PowerPoint-rendered screenshot was not produced in this pass.
- The current PDF backend renders figure context as text/captions/placeholders, not inline image drawing.
