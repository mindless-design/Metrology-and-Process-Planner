# Visual Review Findings

## Gallery

- Location: `tests/output/visual_review_gallery/index.html`
- Manifest: `tests/output/visual_review_gallery/manifest.json`
- Issue inventory: `tests/output/visual_review_gallery/visual_issues.json`
- Visuals reviewed in pass 2: 12

## Pass Summary

Pass 1 generated the existing polish gallery and exposed two high-impact rendering
problems: cross-section leader labels could render outside the canvas, and scene
metadata for legends, scale bars, compression notes, and thin-layer notes was not
visible in the SVG output. The review generator also initially exposed overview
text as clipped because the QA check ignored nonzero SVG viewBox origins.

Pass 2 regenerated the review gallery after fixes. All generated artifacts are now
present and the machine-readable issue inventory is empty.

## Issues Fixed

- `text_clipped`: cross-section label extents now contribute to render source bounds.
- `legend_missing`: SVG cross-section output now renders material legends.
- `scale_bar_missing`: proportional physical cross-section output renders scale bars.
- `compression_unclear`: compressed and exaggerated views render visible notes.
- `thin_layer_invisible`: thin-layer leader/callout metadata is accepted and visible.
- `text_clipped`: visual QA now handles SVG viewBox origins correctly.

## Remaining Limitations

- Automated checks are structural and metadata-driven; they do not replace human
  judgement for aesthetic density or semantic correctness.
- Raster PNG comparison is not part of this pass because the current backend writes
  SVG without a mandatory rasterizer dependency.
- Dense label stress coverage exists in overview tests, but the review gallery only
  includes one site overview fixture.

## Next Polish Tasks

- Add a dense multi-site overview item to the review gallery.
- Add optional raster snapshots when a stable SVG rasterizer is configured.
- Expand process-flow gallery coverage to all generated changed frames, not just the
  representative process-flow frame.
