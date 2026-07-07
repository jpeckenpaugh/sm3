# Concept: Tools as First-Class Enablements

*A reframing of how agents interact with the system.*

---

## The Problem

Currently, an agent's capabilities are defined by two things:

1. **File permissions** in the agent profile (`read: allow`, `edit: { "*.md": allow }`)
2. **Shell scripts** on disk (`scripts/phase_plan.sh`, `git_commit.sh`)

The first is a gate — it says what the agent *may* touch, but not *how*. The second is an implementation detail — a file that exists on disk and gets called by name in a config dict.

Neither is a first-class concept. Neither is queryable, auditable, or composable at runtime.

---

## The Reframing

A **tool** is a named, bounded capability that an agent can invoke. It has:

- A **name** — the identifier used to call it
- A **type** — how it executes (shell script, Python function, HTTP call, etc.)
- A **source** — the definition of what it does (inline code, file path, etc.)
- A **schema** — what arguments it accepts and what it returns
- A **binding** — which phases or contexts it is available in

A tool is not a permission. A permission says "*may* you read `*.md` files?" A tool says "*how* do you read `*.md` files?" Permissions are gates. Tools are mechanisms.

When an agent wants to act, it does not reach for a raw file operation. It invokes a tool:

```
read-project-docs(path="spec.md", scope="sprint")
```

Instead of:

```python
with open("spec.md") as f: ...
```

The tool invocation is recorded. It can be audited. It can be composed. It can be replaced without changing the agent's code.

---

## What Changes

| Concept | Before | After |
|---------|--------|-------|
| Agent capability | File permission (`edit: "*.md"`) | Tool name (`edit-markdown`) |
| Operation | Raw file I/O | Named tool invocation |
| Script management | `.sh` files on disk | `tools` table in SQLite |
| Phase binding | Hardcoded in `config.json` | `phase_tools` join table |
| Observability | None | `tool_calls` log table |
| Permission enforcement | Human convention | Checked against profile at runtime |

---

## Open Questions

1. Should tools be pure SQLite rows, or should they reference files on disk for complex implementations (with the DB row as the index)?
2. How does the agent discover available tools — via a `list-tools` tool, or by reading the `tools` table directly?
3. Should tool invocations be synchronous (blocking) or async (with a signal/callback pattern like Vasuki)?

---

*The Warden watches. The Builder equips. The spiral turns.*
