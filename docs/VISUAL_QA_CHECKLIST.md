# Visual QA Checklist

Use this checklist for `tests/output/visual_review_gallery/` review passes.

## Universal Criteria

- Artifact file exists and is non-empty.
- Image dimensions are valid.
- Main content is visible.
- Selected site, line, point, or stack feature is visible.
- Labels are readable and within canvas/viewBox bounds.
- Labels do not collide severely.
- Important markers are not hidden by labels.
- Warnings or approximation notes are visible where relevant.
- Colors distinguish materials/features clearly.
- Scale, context, or provenance metadata is present where required.

## Site Visuals

- Site label uses human-readable label text, not only a numeric id.
- Raw site image remains unmodified.
- Labeled site image has a readable title strip.
- Site overview shows expanded CAD context.
- Capture box is highlighted.
- Leader connects label to selected capture box.

## Annotation Visuals

- Line annotation endpoints and direction marker are visible.
- Point marker remains visible near the edge of the capture.
- Measurement label and line are readable.
- Annotation contrast is sufficient over the source image.

## Process Visuals

- Material regions are distinguishable.
- Top surface and selected feature context are clear.
- Thin layers are visible or called out.
- Material legend is rendered for cross-section views.
- Compression/exaggeration notes are rendered when used.
- Physical views include scale bars.
- Process-flow frames show the step title/name.

## Automated Checks

The visual review generator records issue objects for missing artifacts, blank SVGs,
invalid dimensions, text outside the canvas/viewBox, label overlap in scene metadata,
missing legends, unclear compression metadata, and selected line/point bounds failures.
