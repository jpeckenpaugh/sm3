# Feature: List Commands

*A concept for the Builder to interpret.*

---

## The Problem

The database contains profiles and components, but there is no way to inspect them from the command line. A developer must query SQLite directly to see what's stored.

## The Goal

`sm list profiles` and `sm list components` provide human-readable output of the database contents, formatted for terminal display.

## The Shape

### `sm list profiles`

Displays each profile's `name`, `version`, and optionally its `header` fields (role, mode, temperature). Colums should be aligned. Example output:

```
Name          Version   Role        Mode    Temperature
──────        ───────   ────        ────    ───────────
scribe        1.0.0     the scribe  all     0.15
builder       1.0.0     the builder all     0.20
...
```

Optional flags:
- `--verbose` or `-v` to show `preamble`, component count, or other details
- `--json` to output raw JSON for programmatic consumption

### `sm list components`

Displays each component's `type`, `name`, and a preview of `content` (truncated if long). Example:

```
Type    Name                   Content Preview
────    ────                   ───────────────
rule    obey-exactly           You do exactly as you are told...
prompt  scribe-domain          You write documents, schemas, and...
...
```

Optional flags:
- Same `--verbose` and `--json` flags as `list profiles`

## What the Builder Must Decide

- Table formatting library or hand-rolled? (Standard library only — `string.format` or f-strings with column width calculation)
- Content truncation length for component preview
- Whether to show component usage count (how many profiles reference this component)
- Color / no color output (ANSI escape sequences are stdlib but may not render everywhere)

## Non-Goals

- Pagination for large result sets (not needed at this scale)
- Sorting/filtering flags (can be added later)
- `sm list profile-components` or other join-table queries (future)

---

*The Scribe maps the territory. The Builder walks it.*
