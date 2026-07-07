# Concept: Database as Source of Truth for Tooling

*What happens when the tool definitions live in SQLite, not on the filesystem.*

---

## The Principle

The same shift we just made for agent profiles applies to tools:

> The database is the source of truth. Files are generated artifacts.

`scripts/phase_plan.sh` is a file. It lives on disk. It is opaque to queries. It cannot be composed, overridden, or inspected without reading the filesystem.

If the tool definition lives in a `tools` table, everything changes.

---

## Proposed Schema

### `tools` — the tool catalog

| Column | Type | Notes |
|--------|------|-------|
| `id` | INTEGER | PK AUTOINCREMENT |
| `name` | TEXT | UNIQUE — the tool identifier, e.g. `git-commit` |
| `type` | TEXT | Executor type: `shell`, `python`, `http`, `query`, `builtin` |
| `source` | TEXT | The content — inline script, Python code, URL, or SQL |
| `schema` | TEXT | JSON Schema describing expected params and return shape |
| `description` | TEXT | Human-readable purpose |
| `created_at` | TEXT | ISO 8601 |
| `updated_at` | TEXT | ISO 8601 |

### `phase_tools` — which tools are available in which phase

| Column | Type | Notes |
|--------|------|-------|
| `id` | INTEGER | PK AUTOINCREMENT |
| `phase` | TEXT | Phase name, e.g. `PLAN`, `WRITE`, `REVIEW` |
| `tool_id` | INTEGER | FK → `tools(id)` |
| `order_idx` | INTEGER | Execution order within the phase |
| `required` | INTEGER | Boolean — does the phase fail if this tool fails? |

### `tool_calls` — the invocation log

| Column | Type | Notes |
|--------|------|-------|
| `id` | INTEGER | PK AUTOINCREMENT |
| `tool_id` | INTEGER | FK → `tools(id)` |
| `profile_id` | INTEGER | FK → `profiles(id)` — who invoked it |
| `phase` | TEXT | Which phase the tool was invoked in |
| `iteration` | INTEGER | Which iteration of the state machine |
| `args` | TEXT | JSON — the arguments passed |
| `result` | TEXT | JSON — stdout, stderr, return code |
| `started_at` | TEXT | ISO 8601 |
| `completed_at` | TEXT | ISO 8601 |
| `success` | INTEGER | Boolean — did it exit cleanly |

---

## What This Enables

### Composability

A phase is no longer a hardcoded for-loop over a config dict. It's a query:

```sql
SELECT t.name, t.type, t.source, t.schema
FROM phase_tools pt
JOIN tools t ON pt.tool_id = t.id
WHERE pt.phase = 'WRITE'
ORDER BY pt.order_idx
```

The phase executor iterates over the result set, checks permissions, dispatches by type, and records each call.

### Overrides without forking

A profile with special needs can reference different tool bindings via `profile_phase_tools` — the same override pattern as `profile_components.params`.

### Observability

`sm status` becomes a SELECT query:

```sql
SELECT COUNT(*) FILTER(WHERE success = 1) as passed,
       COUNT(*) FILTER(WHERE success = 0) as failed
FROM tool_calls
WHERE iteration = (SELECT MAX(iteration) FROM tool_calls)
```

No log files to tail. No signal files to poll. The database *is* the log.

### Runtime enforcement

Before a tool executes:

```sql
SELECT 1 FROM profile_tool_permissions
WHERE profile_id = ? AND tool_id = ? AND allowed = 1
```

If no row exists, the tool is denied — regardless of what the script on disk would do.

---

## Migration Path

The existing `state_machine.py` hardcodes phase scripts in a config dict. A migration could:

1. Create the `tools`, `phase_tools`, and `tool_calls` tables alongside the existing schema
2. Write a migration script that reads `config.json` and populates `tools` and `phase_tools`
3. Add a `sm run --db-sourced` flag that uses the DB definitions instead of the config dict
4. Once proven, make DB-sourced the default and deprecate the file-based path

---

## Open Questions

1. Should `tools.source` store the full content inline, or reference a file path? Inline means the DB is fully portable. File paths mean tools can be large (e.g., a 200-line Python script) without bloating the DB.
2. How do profile-level tool overrides work? A dedicated `profile_tools` table? Or a `params`-style JSON override in `profile_components`?
3. Should the tool executor be a plugin system (load `handlers/<type>.py` at runtime) or a hardcoded dispatch in the phase loop?

---

*The Scribe maps the territory. The Builder walks it. The database holds the map.*
