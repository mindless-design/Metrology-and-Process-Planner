# Rendering Known Limitations

- Visual QA is primarily SVG/scene-metadata based. It catches missing files, blank
  outputs, text outside canvas/viewBox bounds, label metadata overlap, and missing
  legends/notes, but it does not perform pixel-level image-diff grading.
- PNG export remains optional because `SvgCrossSectionRenderer` has no required
  rasterizer dependency. SVG is the canonical generated visual for this review pass.
- The current review gallery covers representative fixtures, not every possible
  session fixture combination.
- Site overview context is generated from available capture targets; very sparse
  sessions may still look visually simple even when technically correct.
