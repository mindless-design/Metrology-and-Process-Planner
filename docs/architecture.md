# Architecture

The plugin is organized as a thin KLayout shell around a pure Python core.

## Layers

`app`
: Composes services, registers commands, and owns plugin startup. App code may
know about adapters, but domain modules should not know about app code.

`ui`
: Qt widgets, dialogs, preview panels, and editor surfaces. UI code should
convert user actions into workflow commands or user intents.

`workflows`
: Explicit state machines for setup, capture, review, repair, measurement, and
export. Workflow modules should be deterministic and easy to unit test.

`domains`
: Data models and business validation for sessions, captures, measurements,
process recipes, solver inputs, and render records.

`rendering`
: Render plans, annotation specs, scene models, and image export contracts. This
layer produces structured descriptions that concrete renderers can consume.

`persistence`
: Session paths, JSON/CSV IO, artifact naming, file safety, and schema migration
entrypoints.

`infrastructure`
: Boundary adapters for KLayout, Qt, logging, diagnostics, file dialogs, and
other environment-specific services.

## Dependency Direction

High-level direction:

```text
KLayout/Qt -> app -> workflows -> domains
                 -> persistence -> domains
                 -> rendering -> domains
```

Forbidden imports:

- `domains` must not import `app`, `ui`, `infrastructure`, KLayout `pya`, or Qt.
- `workflows` must not import KLayout `pya` or Qt.
- `persistence` must not import KLayout `pya` or Qt.
- `rendering` may define render contracts, but concrete KLayout/Qt renderers
  belong in `infrastructure` or `ui`.

## Module Shape

Large concepts should become packages early. Prefer this pattern:

```text
domains/session/
  __init__.py
  captures.py
  capture_geometry.py
  record.py
  setup.py
```

The package `__init__.py` should re-export the stable public API, while the
implementation files stay small and focused.

## Diagnostics

Diagnostics are structured data, not ad hoc print statements. Core services and
adapters should emit `DiagnosticEvent` records that can be collected into a
`DiagnosticsSnapshot`. The eventual Advanced Diagnostics UI should display and
export that snapshot.

## Session Data

The canonical saved data is human-readable JSON. CSV, images, PowerPoint decks,
and derived render outputs are artifacts that can be regenerated or repaired.

Schema changes should be deliberate:

1. Add the target model change.
2. Add a loader that still accepts older saved sessions.
3. Add a migration or compatibility path.
4. Add a golden fixture test before broad refactoring.

## KLayout Boundary

KLayout-specific code imports `pya` lazily, inside adapter functions. Unit tests
must be able to import the package on a machine that does not have KLayout
installed.

Adapters should expose small capabilities such as:

- active layout view lookup
- current viewport and selection
- capture tool activation
- image export
- menu/action registration
- layer and cell discovery

Controllers and workflows should depend on those capabilities, not on raw `pya`
objects.
