# Coding Guidelines

## Keep Features Small

Add features as a vertical slice:

1. Domain model or validation.
2. Workflow command/event.
3. Persistence shape.
4. Adapter or UI wiring.
5. Tests.

Avoid large runtime classes that know about sessions, UI, KLayout view state,
export paths, report building, and recipe logic at the same time.

## Enforced Size Budgets

The normal unit test suite runs `tools.quality_gates`, so these limits are
enforced:

- Source files: 220 lines maximum.
- Test files: 180 lines maximum.
- Public symbols per module: 12 maximum.
- Functions and methods: 50 lines maximum.
- Classes: 140 lines maximum.

When a file approaches the limit, split by responsibility and keep the public API
stable through package `__init__.py` re-exports where useful.

## Docstring Requirements

Every public production module, class, function, and method needs a docstring
summary. The summary must be specific, at least 12 characters, and end with a
period.

Good examples:

```python
def validation_warnings(self) -> tuple[str, ...]:
    """Return warnings for geometry and nested measurements."""
```

Weak examples:

```python
def validation_warnings(self) -> tuple[str, ...]:
    """TODO."""
```

## Model User Intent Explicitly

Dialogs and tools should return values like `ReviewResult`, `UserIntent`, or
workflow commands. They should not directly mutate distant workflow state.

## Use Portable Paths In Session JSON

Session JSON should store artifact paths relative to the session folder. Absolute
paths, drive letters, and `..` traversal are rejected by the persistence layer.

## Error Handling

Failures that affect saved output should become warnings or diagnostics attached
to the session/editor surface. Missing images, failed exports, and invalid
metadata should be visible and recoverable.

## Testing Expectations

Every new domain or persistence feature should have pure Python tests. KLayout
integration tests should stay thin and focus on command dispatch, adapter wiring,
and export smoke behavior.

## Static Analysis Expectations

Run the stdlib quality gate before pushing any change:

```powershell
python -m tools.quality_gates
```

When dev dependencies are installed, run the optional analyzer suite:

```powershell
python -m tools.static_analysis --fail-on-missing
```

Do not "fix" dynamic Qt or KLayout findings by weakening the core architecture.
Keep dynamic behavior in `ui` and `infrastructure/klayout`, then expose typed
protocols or plain data models to the rest of the system.
