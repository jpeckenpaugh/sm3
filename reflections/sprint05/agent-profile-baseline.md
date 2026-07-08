# Agent Profile Baseline — Sprint 05

*A capture of the current state of all agent profile representations before the cleanup pass. For A/B comparison after the component composition system is fully reconciled.*

---

## The Three Representations

The agent profile system currently exists in three forms, each at a different level of staleness:

### Representation A: Component Composition (the designed canonical source)

| Location | Contents | Status |
|----------|----------|--------|
| `profiles/*.json` | 16 profile definitions with name, version, header, permissions, base_profile | ✅ Clean |
| `components/prompts/*.json` | 22 reusable prompt components (mode instructions, domain descriptions, preambles) | ✅ Clean, though CONFIRM_BOOTSTRAP is duplicated across all 8 mode components |
| `components/rules/*.json` | 1 rule component (`obey-exactly`) | ✅ Clean |
| `profile-components/*.json` | 16 files linking profiles to their component references | ✅ Clean |

**How it works:** `sm generate agent <name>` reads `profiles` from the database, walks the `base_profile` inheritance chain via `_resolve_inheritance_chain()`, collects all `profile_components` from each level via `_assemble_components_for_profiles()`, merges by component_id (child overrides parent), sorts by `order_idx`, and joins the content into an assembled body. The `body` column is **not read** in this path.

### Representation B: SQLite `profiles.body` column (the stale cache)

```sql
CREATE TABLE profiles (
    ...
    body TEXT DEFAULT '',
    ...
);
```

The `body` column is written by `seed.py` line 80 from `profile.get("body", "")`. The on-disk JSON profiles (`profiles/*.json`) **do not have a `body` field** — they use component composition instead. Therefore, `seed.py` writes an empty string to `body` for every profile.

**The `body` column is never read by any code path:**
- `cli.py` `cmd_generate_agent()` selects `name, version, header, permissions` — **not** `body`
- `pipeline/dispatch.py` does not touch the `profiles` table
- `pipeline/engine.py` does not touch the `profiles` table

The `body` column is a **zombie** — written with empty data, never read, occupying space.

### Representation C: Generated `.md` files in `.opencode/agents/` (inconsistent snapshots)

| File | Generated From | Status | Problem |
|------|---------------|--------|---------|
| `saraswati.md` | Spiral 5 archetype definition | ✅ Manual, but correct | Hand-authored, not generated from database |
| `matsya.md` | Spiral 5 archetype definition | ✅ Manual, but correct | Hand-authored, not generated from database |
| `kurma.md` | Spiral 5 archetype definition | ✅ Updated with Pulse Check | Hand-authored, not generated from database |
| `warden-REVIEW.md` | Hand-generated Sprint 04 | ⚠️ Stale | Permissions mismatch with `profiles/warden-REVIEW.json — has signals/* instead of sprint/*/review.md + .escalation/* |
| `warden.md` | Hand-generated Sprint 04 | ⚠️ Stale | Has `edit: { "signals/*": allow }` which matches none of the warden profiles on disk |
| `code-agent.md` | Sprint 0 prototype | ❌ Legacy | `description: "Write docs only"` with `temperature: 0.2` — superseded by Matsya |
| `doc-agent.md` | Sprint 0 prototype | ❌ Legacy | `description: "Write docs only"` with `temperature: 0.1` — superseded by Saraswati |
| `the-scribe.md` | Sprint 0 prototype | ❌ Legacy | Superseded by Saraswati archetype |
| `the-parent.md` | Sprint 04 naming | ⚠️ Legacy | Superseded by Kurma with Pulse Check section |
| `agent-01.md` | Fallen machine | ❌ Legacy | Has `bash: allow`, `edit: allow` — unrestricted permissions from the old era |

**Missing derived agent files:**

The following derived profiles have no generated `.md` file in `.opencode/agents/`:

| Profile | pipeline_states reference | File exists? |
|---------|--------------------------|-------------|
| `scribe-PLAN` | `POPULATE_BACKLOG` | ❌ |
| `scribe-SPRINT_PLANNING` | `SPRINT_PLANNING` | ❌ |
| `scribe-DESIGN` | `DESIGN` | ❌ |
| `scribe-ARCHITECT` | `ARCHITECT` | ❌ |
| `builder-ENGINEER` | `ENGINEER` | ❌ |
| `builder-TEST` | `TEST_BUILD` | ❌ |
| `warden-TEST_RUN` | `TEST_RUN` | ❌ |
| `scribe-REVIEW` | `REVIEW` | ❌ |
| `warden-GATE` | `SPRINT_GATE` | ❌ |

These 9 derived profiles are defined in the database and referenced by `pipeline_states.agent_name`, but have no agent files. The OpenCode runtime requires `<name>.md` files in `.opencode/agents/` to dispatch to them.

---

## Current Generator Behavior

When `sm generate agent <name>` runs (lines 559–619 of `cli.py`):

1. Loads `name, version, header, permissions` from `profiles` table
2. Walks `base_profile` chain from child to root
3. Collects `profile_components` from each level, merging by component_id
4. Sorts by `order_idx`, joins content with `\n\n`
5. Renders: YAML frontmatter (description, mode, temperature, permission_yaml) + assembled body
6. Writes to `.opencode/agents/<name>.md`

The `body` column is **not used**. The `preamble` column is **not used**. The assembly comes entirely from the component composition system.

---

## Duplication Patterns Identified

### Pattern 1: CONFIRM_BOOTSTRAP boilerplate

Every mode-specific component contains 15–20 lines of identical boilerplate defining the handshake protocol. This text is duplicated across all 8 mode components. If the handshake format changes (e.g., Pulse Check), all 8 must be updated individually.

**Current instances:**
- `components/prompts/scribe-mode-plan.json`
- `components/prompts/scribe-mode-design.json`
- `components/prompts/scribe-mode-architect.json`
- `components/prompts/scribe-mode-review.json`
- `components/prompts/scribe-mode-sprint-planning.json`
- `components/prompts/builder-mode-engineer.json`
- `components/prompts/builder-mode-test.json`
- `components/prompts/warden-mode-review.json`
- `components/prompts/warden-mode-test-run.json`
- `components/prompts/warden-mode-gate.json`

~15 lines × 10 files = ~150 lines of identical text.

### Pattern 2: Mode-specific components duplicate file_contracts

Each mode-specific component lists its INPUT and OUTPUT contracts with descriptions. These same contracts are defined in the `file_contracts` database table. Example — `scribe-mode-plan.json` says:

```
INPUT1: Concept or requirements document
OUTPUT1: Backlog directory with decomposed feature files
OUTPUT2: Sprint brief document
```

Meanwhile, `file_contracts` for `POPULATE_BACKLOG` has:
```
direction: input,  pattern: concept.md
direction: output, pattern: backlog/ft-*.md
direction: output, pattern: sprint/{:03d}/brief.md
```

These are two sources of truth for the same information. If one changes and the other doesn't, the agent sees different contracts than the engine enforces.

### Pattern 3: Permission inheritance duplication

Base profile `builder.json` declares `check_syntax: allow`. Derived profile `builder-ENGINEER.json` also declares `check_syntax: allow` in its own permissions block. The `cmd_generate_agent()` function uses the **derived profile's permissions only** (line 582: `permissions = json.loads(permissions_json)`) — it does not merge base and derived permissions.

This means derived profile permissions must duplicate the base's permissions to have them in the generated agent file. Currently this duplication is maintained manually.

### Pattern 4: Preamble column unused

The `profiles` table has a `preamble TEXT DEFAULT ''` column. It is written by `seed.py` from `profile.get("preamble", "")` but is **never read** by `cmd_generate_agent()`. The preamble concept was from the Sprint 0 design and was superseded by component composition.

### Pattern 5: Sprint 0 legacy files in agent directory

Five files in `.opencode/agents/` are Sprint 0 artifacts from the fallen machine era:
- `agent-01.md` — has `bash: allow`, `edit: allow` (unrestricted)
- `code-agent.md` — superseded by Matsya
- `doc-agent.md` — superseded by Saraswati
- `the-scribe.md` — superseded by Saraswati
- `the-parent.md` — superseded by Kurma

These files may still be referenced by agent dispatch if an old state machine configuration points to them.

---

## Summary: What Needs Cleanup

| # | Item | Current State | Target |
|---|------|---------------|--------|
| 1 | `body` column in `profiles` | Written with empty string, never read | Remove column, remove from `seed.py` |
| 2 | `preamble` column in `profiles` | Written from JSON but never read | Remove column, remove from `seed.py` |
| 3 | CONFIRM_BOOTSTRAP in mode components | Duplicated across 10 files (~150 lines) | Extract to shared `rule/bootstrap-protocol` component |
| 4 | Permission inheritance | `cmd_generate_agent()` uses derived permissions only; no merge with base | Merge base + derived permissions for generated agent files |
| 5 | Missing derived agent files | 9 pipeline agents have no `.md` in `.opencode/agents/` | Generate all with `sm generate agents` (plural) |
| 6 | Legacy agent files | `agent-01.md`, `code-agent.md`, `doc-agent.md`, `the-scribe.md`, `the-parent.md` | Archive or remove |
| 7 | warden-REVIEW.md | Hand-generated, stale, permissions don't match profile JSON | Regenerate from component composition |
| 8 | warden.md | Hand-generated, permissions don't match profile JSON | Regenerate from component composition |
| 9 | Input/Output in two places | Both mode components and `file_contracts` define the same contracts | Single source of truth — generate mode component content from `file_contracts` |

---

## Appendix A: Generated Agent Files — Fresh Baseline

All 9 derived agent files were generated with `sm generate agent --db matsya.db` on 2026-07-08 after the Sprint 05 tool additions. The generator assembled them from the component composition system (not from `body` column, which is empty).

### scribe-* agents (5 files)

All share the same structure:
- **Frontmatter:** `description: "the scribe — MODE mode"`, `mode: all`, `temperature: 0.15`, permissions from `profiles/<name>.json` (inherits script.json universal tools + adds `read_pulse: allow`)
- **Body assembly:** `rule/obey-exactly` + `prompt/scribe-preamble` + `prompt/scribe-domain` + `prompt/scribe-mode-<mode>`
- **CONFIRM_BOOTSTRAP:** Inline within each mode component — identical except mode name
- **Closing line:** "The Scribe gives form to intention before it becomes implementation. You write documents, schemas, and handoff specifications. You do not write executable code."

| File | Mode | Components | Lines |
|------|------|-----------|-------|
| `scribe-PLAN.md` | PLAN | 4 | 79 |
| `scribe-SPRINT_PLANNING.md` | SPRINT_PLANNING | 4 | 84 |
| `scribe-DESIGN.md` | DESIGN | 4 | 69 |
| `scribe-ARCHITECT.md` | ARCHITECT | 4 | 69 |
| `scribe-REVIEW.md` | REVIEW | 4 | 72 |

### builder-* agents (2 files)

Same structure with `temperature: 0.2`, permissions from builder base (+ `check_syntax`, `lint_code`):
- **Closing line:** "The Builder receives specifications and produces working implementations. You write code, tests, and deployment scripts. You do not modify specifications."

| File | Mode | Components | Lines |
|------|------|-----------|-------|
| `builder-ENGINEER.md` | ENGINEER | 4 | 76 |
| `builder-TEST.md` | TEST_BUILD | 4 | 69 |

### warden-* agents (2 files)

Same structure with `temperature: 0.1`, permissions from warden base (+ domain-specific tools):
- **Closing line:** "You observe and reflect. You do not create artifacts. You do not modify state. Your output is reflection, not instruction."

| File | Mode | Components | Lines |
|------|------|-----------|-------|
| `warden-TEST_RUN.md` | TEST_RUN | 3 | 61 |
| `warden-GATE.md` | SPRINT_GATE | 3 | 77 |

### Observations from the fresh generation

1. **The generator works.** All 9 files assemble correctly from the component composition pipeline. The `body` column is irrelevant to the generation process.

2. **Permissions are not inherited at YAML level.** The generator uses only the derived profile's `permissions` JSON. The three universal tools (`search_files`, `list_files`, `file_tree`) are declared in the base profiles (`scribe.json`, `builder.json`, `warden.json`) but the generated files do **not** include them — because the generator does not merge base + derived permissions. This is the permission inheritance duplication (Pattern 3).

   **Consequence:** The generated `scribe-PLAN.md` has `read_pulse: allow` but NOT `search_files`, `list_files`, or `file_tree`. Those tools are declared in `profiles/scribe.json` but the generator does not merge them.

3. **Universal tools are invisible to derived agents.** Despite being declared in base profiles, the universal tools (`search_files`, `list_files`, `file_tree`) do not appear in any generated derived agent file. This means they may not be accessible at runtime unless the OpenCode tool resolution checks base profiles independently of the generated file — which is unlikely.

   **This is a bug in the generator.** It needs to merge base + derived permissions when building the frontmatter.

### Pre-existing generated files (not regenerated)

These five files were hand-authored, not generated from the database:

| File | Status | Permission issue |
|------|--------|-----------------|
| `saraswati.md` | ✅ Correct | Hand-authored, matches `profiles/saraswati.json` (except no tools declared — Spiral 5 agents don't use the component system) |
| `matsya.md` | ✅ Correct | Hand-authored, matches `profiles/matsya.json` |
| `kurma.md` | ✅ Correct (updated with Pulse Check) | Hand-authored, matches `profiles/kurma.json` |
| `warden-REVIEW.md` | ⚠️ Stale | Has `edit: { "signals/*": allow }` but `profiles/warden-REVIEW.json` specifies `edit: { "sprint/*/review.md": allow, ".escalation/*": allow }` |
| `warden.md` | ⚠️ Stale | Has `edit: { "signals/*": allow }` but `profiles/warden.json` has no edit permissions |

### Legacy files (Sprint 0 / fallen machine)

| File | Problem |
|------|---------|
| `agent-01.md` | `bash: allow`, `edit: allow` — unrestricted permissions |
| `code-agent.md` | Superseded by Matsya |
| `doc-agent.md` | Superseded by Saraswati |
| `the-scribe.md` | Superseded by Saraswati |
| `the-parent.md` | Superseded by Kurma with Pulse Check |

---

## Appendix B: Database State Confirmed

From Matsya's database inspection:

| Table | Rows |
|-------|------|
| `profiles` | 16 |
| `components` | 23 |
| `profile_components` | 24 |
| `pipeline_states` | 10 |

**`body` column:** Empty for all 16 profiles (`length(body) = 0`). **`preamble` column:** Empty for all 16 profiles.

The component composition system is the sole source of truth. The `body` and `preamble` columns are zombie columns — written but never read.

---

## Appendix C: Clean Init Instructions

From project root:

```bash
source .venv/bin/activate
python3 -m genesis_sm.seed                                 # 1. Seed DB
for name in $(sqlite3 matsya.db "SELECT name FROM profiles ORDER BY name;"); do
  python3 -m genesis_sm.cli --db matsya.db generate agent "$name"  # 2. Generate agents
done
```

**Discovered wrinkle:** Seed order is alphabetical by filename. Derived profiles (e.g., `builder-ENGINEER.json`) load before their base profiles (e.g., `builder.json`) because `builder-ENGINEER` < `builder` in ASCII sort. This produces "Base profile not found" warnings at seed time but does not affect runtime behavior (profiles are resolved lazily at composition time).

---

*Baseline captured by Saraswati, Sprint 05, 2026-07-08. Before the cleanup pass. For A/B comparison after changes. Database state confirmed by Matsya.*
