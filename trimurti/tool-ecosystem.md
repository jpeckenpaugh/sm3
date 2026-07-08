# The Tool Ecosystem

*Empowering the pantheon without expanding permissions. A design by Saraswati, for Brahma's approval.*

---

## The Principle

Every agent in the system has tightly scoped permissions. This prevents damage but also prevents action. Custom tools bridge the gap — they are **named, bounded capabilities** that let agents do what they need without expanding their ambient authority.

A tool is not a permission. A tool is a **single-purpose action** with defined inputs and defined effects. An agent can use a tool but cannot use the tool's mechanism for any other purpose.

---

## The Tools

### Built-in tools (OpenCode runtime)

| Tool | Spiral 5 (Trimurti) | Spiral 1 (operational) | Risk |
|------|-------------------|----------------------|------|
| **webfetch** | ✅ unrestricted | ✅ domain-restricted | Low. Read-only. No write or execute. |
| **websearch** | ✅ | ✅ | Low. Read-only results. |
| **question** | ✅ | ❌ | Agents run non-interactive. No one hears them. |

### Custom tools (defined in `.opencode/tools/`)

| Tool | Agents | What it does |
|------|--------|-------------|
| **check_syntax** | builder-ENGINEER, builder-TEST | `py_compile.compile(filepath)` — verifies Python syntax without executing |
| **archive_features** | warden-GATE | Moves `backlog/ft-*.md` → `backlog/archive/{n}/` after sprint completes |

---

## Per-Agent Permissions

### Spiral 5 — Trimurti (already configured)

```
Saraswati: read, edit: *.md/*.sql/*.json, webfetch, websearch, question
Matsya:    read, edit: *.py/*.sh/*.sql/*.md/*.json/*.yaml/*.yml/*.ts, webfetch, websearch, question
Kurma:     read, edit: .escalation/*, webfetch, websearch, question
```

### Spiral 1 — Operational agents

#### scribe domain

```
scribe-PLAN, scribe-DESIGN, scribe-ARCHITECT, scribe-REVIEW:

permission:
  "*": deny
  read: allow
  edit:
    "*.md": allow
    "*.sql": allow
    "*.json": allow
  webfetch:
    "https://docs.python.org/*": allow
    "https://pypi.org/*": allow
    "https://opencode.ai/docs/*": allow
    "*": deny
  websearch: allow
```

Rationale: Scribes need to research documentation for specifications and designs. They do not need to ask questions (non-interactive). They write only documents.

#### builder domain

```
builder-ENGINEER, builder-TEST:

permission:
  "*": deny
  read: allow
  edit:
    "*.py": allow
    "*.sh": allow
    "*.sql": allow
    "*.md": allow
    "*.json": allow
  webfetch:
    "https://docs.python.org/*": allow
    "https://pypi.org/*": allow
    "https://fastapi.tiangolo.com/*": allow
    "*": deny
  websearch: allow
```

Builders need to research API documentation and check package pages. The `check_syntax` tool is available to verify their Python output without executing it.

#### warden domain

```
warden-TEST_RUN, warden-GATE:

permission:
  "*": deny
  read: allow
  edit:
    "*.md": allow  (warden-TEST_RUN: test report)
    ".escalation/*": allow  (warden-GATE: escalation)
  webfetch:
    "https://docs.python.org/*": allow
    "https://opencode.ai/docs/*": allow
    "*": deny
  websearch: allow
```

Wardens need to verify external references. warden-GATE also has `archive_features` tool available for archiving completed features.

#### courier and keeper

```
courier:
permission:
  "*": deny
  read: allow
  edit:
    "signals/*": allow
  webfetch: deny
  websearch: deny

keeper:
permission:
  "*": deny
  read: allow
  edit:
    "*.md": allow
  webfetch:
    "https://docs.python.org/*": allow
    "*": deny
```

Courier needs no research tools — it carries signals faithfully. Keeper may reference preservation standards.

---

## Tool Implementation Status

| Tool | Status | Owner | Location |
|------|--------|-------|----------|
| `check_syntax` | ⬜ Not built (spec in ft007) | Matsya | `.opencode/tools/check_syntax.ts` + `scripts/check_syntax.py` |
| `archive_features` | ⬜ Not built (spec in trimurti/tool-archive-features.md) | Matsya | `.opencode/tools/archive_features.ts` + `scripts/archive_features.sh` |

Both tools follow the same pattern:
1. TypeScript definition in `.opencode/tools/` (tool name = filename)
2. Backing script in `scripts/` (Python or shell, Matsya's domain)
3. No `bash: allow` needed — the tool definition is the permission boundary
4. No `tools:` declaration in agent profiles — tools are automatically available

---

## What Does Not Change

- No agent gains `bash: allow`
- No agent gains broad `edit` access outside their domain
- No agent gains the ability to execute code
- The principle of least privilege is preserved
- The permission boundaries defined in Sprint 04 remain intact

---

*Designed by Saraswati, for Brahma's approval. Built by Matsya. Watched by Kurma.*
