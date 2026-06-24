# Test Strategy

## Pure Python Tests

- recipe parsing and validation
- process solver behavior
- session JSON round trip
- CSV export
- naming and path policy
- measurement validation
- render-spec generation

## Golden Or Characterization Tests

- known process recipe produces expected stack intervals
- known session JSON loads and saves without schema loss
- known capture metadata produces expected report model
- known process-flow input produces expected frame list

## KLayout Integration Tests

- menu registration
- command dispatch
- source-view binding
- capture tool activation
- image export smoke tests
- 2.5D script generation
- cross-section export smoke tests

These tests should be isolated from the core suite so regular contributors can
run the pure Python suite without installing KLayout.

## UI Smoke Tests

- setup guide opens and advances
- capture review save/discard paths
- session editor opens saved sessions
- recipe editor validates and saves
- dialogs fit common screen sizes

## Reporting Tests

- build PowerPoint from sample session
- missing image placeholder behavior
- measurement slides follow parent capture
- process-flow slides load from saved frame metadata

## Release Tests

- package manifest excludes development files
- staged package contains `grain.xml`, `pymacros`, and `python`
- package archive can be built
- release check validates versions and required gates
