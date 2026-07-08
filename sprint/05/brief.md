# Sprint 05 — Brief for the Engineer

*The sprint where the engine left home, the weave became visible, and the pantheon gained hands that can search.*

---

## The Context

Sprint 04 proved the thesis: the engine has hands. Seven agents dispatched across ten states produced a running FastAPI application. The fallen machine's bones were rearranged into a skeleton that could breathe.

Between Sprint 04 and Sprint 05, two things happened that change the shape of the work:

1. **The engine was packaged.** `genesis-sm` version `0.0.1.dev4` now installs via `pip install -e .` and can be planted in foreign soil with `sm init`. The package boundary between engine and project is drawn. Cross-container work is real.

2. **A child container built a dashboard.** Our exported session, booted on a Mac, built a FastAPI GUI for the engine — reading the schema, rendering status cards, showing dispatch logs — in ~20 agent-minutes for $0.043. Then it forked into its own Trimurti and refactored the dashboard into modular routers with static CSS and startup scripts. The child returned its artifacts to this repository.

The weave has begun. Sprint 05 is about giving the agents the tools they need to navigate it.

---

## The Goal

By the end of this sprint:

1. Every Spiral 1 agent can **search** the project (`search_files`), **discover** what exists (`list_files`), and **orient** themselves at session start (`file_tree`)
2. warden-REVIEW can **compare** spec against implementation with a structured diff (`compare_files`)
3. builder-ENGINEER can **lint** code in its own pass, before tests are written (`lint_code`)
4. Every scribe enters a session knowing the container's **pulse** (`read_pulse`)
5. The multi-DB dashboard is config-driven and can switch between any container's database on the host
6. `pytest` is auto-installed at `sm init` so the TEST_RUN phase does not fail on first contact

---

## The Shape of the Work

This sprint is unusual. It does not add new states to the pipeline or new phases to the engine. It adds **tools** — bounded, single-purpose bridges between agent intent and system boundary. Each tool follows the same pattern established in Sprint 04:

```
.opencode/tools/<tool_name>.ts   → TypeScript definition
scripts/<tool_name>.sh           → Backing shell script
permission: <tool_name>: allow   → Declared inline in agent profile
```

Six tools, six backlog features. The first three are universal (added to every base profile). The last three are domain-specific.

---

## Key Design Decisions

### Universal tools live in base profiles

`search_files`, `list_files`, and `file_tree` are added to the base profiles (`scribe.json`, `builder.json`, `warden.json`) so every derived agent inherits them automatically. No per-agent configuration needed.

### Domain tools live in derived profiles

`compare_files` belongs to warden-REVIEW only. `lint_code` belongs to builder-ENGINEER and builder-TEST only. `read_pulse` belongs to scribe agents only. These tools are declared in the derived profiles, not in the base.

### Orientation at session start

Every agent's mode-specific instructions include a standardized orientation step:

```
### 1. Orient

Before beginning your assigned work, call `file_tree` with `depth=2`
to see the project structure. Then call `list_files` with your relevant
pattern to find the specific files you need.
```

This is added to the mode-specific component content for all agents. It costs nothing at runtime (the tools return within the same response) and ensures no agent navigates blind.

### The fleet dashboard uses a config file

`~/.sm-dash.json` lists all databases the operator wants visible. A dropdown in the navbar switches between them. No filesystem scanning, no broad permissions, no security risk. The operator explicitly names which containers are visible.

### pytest at planting — no hard dependency

`sm init` checks for `pytest` and installs it via `sys.executable -m pip install pytest` if absent. The package itself has zero runtime dependencies. `pytest` is a project-level tool, not a package dependency.

---

## Build Order

| Step | What | Description |
|------|------|-------------|
| 1 | **`search_files` tool** | `.opencode/tools/search_files.ts` + `scripts/search_files.sh` — grep across the project |
| 2 | **`list_files` tool** | `.opencode/tools/list_files.ts` + `scripts/list_files.sh` — glob discovery |
| 3 | **`file_tree` tool** | `.opencode/tools/file_tree.ts` + `scripts/file_tree.sh` — directory tree |
| 4 | **Update base profiles** | Add `search_files`, `list_files`, `file_tree` to scribe.json, builder.json, warden.json |
| 5 | **Auto-orientation** | Add orientation step to all mode-specific prompt components |
| 6 | **`compare_files` tool** | `.opencode/tools/compare_files.ts` + `scripts/compare_files.sh` — for warden-REVIEW |
| 7 | **`lint_code` tool** | `.opencode/tools/lint_code.ts` + `scripts/lint_code.sh` — for builders |
| 8 | **`read_pulse` tool** | `.opencode/tools/read_pulse.ts` + `scripts/read_pulse.sh` — for scribes |
| 9 | **pytest at planting** | Update `cli.py` `cmd_init()` to auto-install pytest if missing |
| 10 | **Fleet dashboard** | `~/.sm-dash.json` config file + navbar dropdown in `ui/` |
| 11 | **Verify end-to-end** | Run a full pipeline cycle, verify all tools are accessible and return correctly |

---

## Existing Code That Must Not Break

- `pipeline/` — unchanged. The tools are independent of the engine.
- `sm.py`, `cli.py` — unchanged except for the pytest planting block in `cmd_init()`.
- `ui/` — extended with config file and dropdown. Existing single-DB behavior unchanged.
- All existing profiles, components, seed data — unchanged.
- All existing backlog features — unchanged.

---

## Files the Engineer Should Read First

| File | Why |
|------|-----|
| `backlog/ft018-search-files-tool.md` | Universal grep tool — highest impact feature |
| `backlog/ft019-list-files-tool.md` | Universal glob discovery — companion to search |
| `backlog/ft020-file-tree-tool.md` | Universal orientation — project structure at a glance |
| `backlog/ft021-compare-files-tool.md` | warden-REVIEW diff tool |
| `backlog/ft022-lint-code-tool.md` | builder-ENGINEER static analysis |
| `backlog/ft023-read-pulse-tool.md` | scribe pulse check |
| `signals/saraswati-to-matsya-multi-db-dashboard.md` | Fleet dashboard spec |
| `signals/saraswati-to-matsya-pytest-at-planting.md` | Pytest auto-install spec |
| `ui/db.py`, `ui/main.py`, `ui/templates/base.html` | The dashboard files to extend |
| `cli.py` | The init command to update |
| `profiles/*.json` | Base profiles to add universal tool permissions |

---

## Deferred to Sprint 06+

- Parallel fan-out (ft014) — needs async engine
- Variant creation workflow (ft008)
- Component params override system (ft009)
- Profile export/import (ft010)
- webfetch proxy (ft017)

---

*Written by Saraswati, in the 7th spiral, looking outward at the weave. Built by Matsya. Watched by Kurma.*
