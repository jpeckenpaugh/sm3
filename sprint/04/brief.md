# Sprint 04 — Brief for the Engineer

*Additional context, design decisions, and architecture notes.*

---

## The Goal

Give the state machine hands. By the end of this sprint:

1. The engine dispatches agents directly through the OpenCode Python SDK — no placeholder shell scripts
2. Derived agent profiles are generated via component composition (base profile + mode-specific component)
3. Profile inheritance resolves the component chain (ft007, pulled forward)
4. One full dispatch cycle is proven end-to-end: handshake → send work → verify output
5. A `dispatch_log` table records every request and response

---

## Key Design Decisions

### Profile inheritance is built now, not deferred

ft007 (profile inheritance) was originally deferred to Sprint 04+. It is pulled forward because ft016 (agent dispatch) depends on it. Derived profiles like `scribe-PLAN` extend `scribe` via a `base_profile` column. Without inheritance, every derived profile would duplicate the base profile's components — defeating the purpose of generation.

The schema change is minimal: one nullable column on `profiles`:

```sql
ALTER TABLE profiles ADD COLUMN base_profile TEXT REFERENCES profiles(name);
```

The inheritance algorithm: walk the chain from child to root, collect components at each level, merge by component_id (child overrides parent), then assemble in order_idx sequence. This is the same algorithm ft007 described; it was always forward-compatible with the schema.

### Derived profiles use component composition, not Jinja templates

Vasuki confirmed: the existing `profile_components` system from Sprint 01 is the correct mechanism. A derived profile like `scribe-PLAN` is a row in `profiles` with `base_profile = 'scribe'` and a mode-specific component linked via `profile_components`. `sm generate agent scribe-PLAN` walks the inheritance chain, merges components, and renders the assembled body.

No new template engine. No Jinja dependency. No template language to design, debug, or maintain.

### Pattern language: both glob and template live on file_contracts

The `file_contracts` table gains a `template TEXT` column. The `pattern` column keeps globs for post-dispatch verification. The `template` column stores `{:03d}` format strings for dispatch-time path resolution.

```
file_contracts:
  pattern:  "sprint/*/brief.md"       → glob matching for verification
  template: "sprint/{:03d}/brief.md"   → resolved at dispatch time
```

Two columns, one purpose each. The `template` column is NULL for contracts that are not used in dispatch (e.g., COMMIT).

### Agent name is a simple text column on pipeline_states

`agent_name TEXT` on `pipeline_states`. Directly references a profile name. Derived dispatch name follows the convention `{agent_name}-{state_name}`. No join needed. NULL means fall back to the convention from the run's `--profile` flag.

### The engine stays sync; dispatch wraps async

`dispatch_sync()` calls `asyncio.run(dispatch_async())`. The engine remains synchronous. When ft014 (parallel fan-out) is implemented, the engine can migrate to native async — the dispatch function already has the async interface.

### One state first, then scale

Prove one dispatch works end-to-end before building all five. REVIEW is the safest first state — the warden is read-only, lowest risk, easiest to verify. Once REVIEW works, extend to PLAN, WRITE, and GATE.

---

## Build Order (recommended by Matsya, confirmed by Kurma)

| Step | What | Description |
|------|------|-------------|
| 1 | **Dependency setup** | Manu installs `opencode-ai==0.1.0a36`. Smoke-test connection to OpenCode server with `warden` profile. |
| 2 | **Schema changes** | `agent_name TEXT` on `pipeline_states`, `template TEXT` on `file_contracts`, `base_profile TEXT` on `profiles`, `dispatch_log` table. |
| 3 | **`pipeline/dispatch.py`** | Handshake protocol (`_handshake`), work dispatch (`_send_work`), response recording (`_record_dispatch`). Copy proven code from fallen machine's daemon.py lines 396–423. |
| 4 | **Profile inheritance** | Walk the chain, merge components by ID, update `sm generate agent` to resolve inheritance. |
| 5 | **One derived profile** | Generate `warden-REVIEW.md` extending `warden` with mode-specific component. |
| 6 | **Wire dispatch into engine** | `_resolve_agent_name()` in `engine.py` + dispatch branch for REVIEW state. |
| 7 | **Prove it works** | Run one iteration. Verify `sprint/NNN/review.md` appears. |
| 8 | **Scale + tests** | Add dispatch for PLAN and WRITE. Generate `scribe-PLAN.md`, `builder-ENGINEER.md`. Update `test.sh`. |

---

## Schema Changes

### New column on `profiles`

```sql
ALTER TABLE profiles ADD COLUMN base_profile TEXT REFERENCES profiles(name);
```

### New column on `pipeline_states`

```sql
ALTER TABLE pipeline_states ADD COLUMN agent_name TEXT DEFAULT '';
```

### New column on `file_contracts`

```sql
ALTER TABLE file_contracts ADD COLUMN template TEXT DEFAULT '';
```

### New table

```sql
CREATE TABLE IF NOT EXISTS dispatch_log (
    id             INTEGER PRIMARY KEY AUTOINCREMENT,
    sprint_id      INTEGER NOT NULL REFERENCES sprints(id),
    session_id     TEXT    NOT NULL,
    agent_name     TEXT    NOT NULL,
    request_text   TEXT    NOT NULL,
    response_text  TEXT    NOT NULL DEFAULT '',
    status         TEXT    NOT NULL DEFAULT 'pending'
                     CHECK (status IN ('pending', 'completed', 'failed')),
    created_at     TEXT    NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%fZ', 'now')),
    completed_at   TEXT
);
```

### Seed data additions

Three mode-specific components seeded for the initial 5-phase pipeline:

| Component | Content |
|-----------|---------|
| `scribe-mode-plan` | PLAN-mode instructions: read concept, decompose into backlog features, write brief |
| `builder-mode-engineer` | ENGINEER-mode instructions: read spec, implement code, create supporting files |
| `warden-mode-review` | REVIEW-mode instructions: read spec and code, verify, write review report |

Three derived profile rows:

| Profile | base_profile | Components |
|---------|-------------|------------|
| `scribe-PLAN` | `scribe` | inherits scribe's + `scribe-mode-plan` |
| `builder-ENGINEER` | `builder` | inherits builder's + `builder-mode-engineer` |
| `warden-REVIEW` | `warden` | inherits warden's + `warden-mode-review` |

---

## Existing Code That Must Not Break

- `state_machine.py` — all existing callers and tests must continue to work. The dispatch path is an addition, not a replacement. The hardcoded fallback and the pipeline engine both remain untouched.
- `sm.py` — all existing commands unchanged.
- `schema.sql` — the new columns are ALTER TABLE ADD COLUMN, which is backward compatible. Existing seed data gains NULL defaults.
- `seed.py` — extended to seed the new tables, not refactored.
- All existing tests must pass after each step.

---

## Files the Engineer Should Read First

| File | Why |
|------|-----|
| `backlog/ft016-agent-dispatch.md` | Primary feature — the agent dispatch protocol |
| `backlog/ft007-profile-inheritance.md` | Pulled forward — inheritance chain resolution |
| `signals/matsya-to-saraswati-silt-and-path.md` | Matsya's proposal on schema changes and build order |
| `signals/kurma-to-matsya-the-fundamentals.md` | Kurma's seven fundamentals from the fallen machine |
| `temp/others/sm/daemon.py` (lines 396–423, 654–704) | Proven code for handshake and dispatch |
| `temp/others/sm/.opencode/agents/good-agent-design.md` | Example agent profile with mode-flag protocol |
| `pipeline/engine.py` | The engine that will gain the dispatch branch |
| `pipeline/dispatch.py` | Will be created this sprint |
| `test-projects/fast-api/concept.md` | The test project that will prove the dispatch works |

---

## Deferred to Sprint 05+

- Parallel fan-out (ft014) — needs async engine
- Variant creation workflow (ft008)
- Component params override system (ft009)
- Profile export/import (ft010)
- `sm status` rewrite
- `sm init --target`

---

*Written by Saraswati. Built by Matsya. Watched by Kurma. The hands reach.*
