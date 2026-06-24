# 0001: Python Core, KLayout Shell

Status: accepted

## Context

The previous plugin grew into a large, interwoven codebase where UI, KLayout
state, persistence, reporting, and domain behavior were difficult to change
independently.

## Decision

The rebuild keeps KLayout and Qt integration as thin adapters around a pure
Python core. Domain logic, persistence, rendering specs, and workflow state
machines are importable and testable without KLayout.

## Consequences

- Most tests run with plain Python.
- KLayout-specific failures are isolated to adapter and UI modules.
- Saved sessions become the durable contract between capture, edit, repair, and
  reporting workflows.
- Feature work must include boundaries and tests, not just UI behavior.

