# Sprint 05 — Features

*Give the pantheon tools. Eleven steps, ordered by dependency. Build in this sequence.*

---

| # | Feature | Source | Depends on |
|---|---------|--------|------------|
| 1 | **`search_files` tool** | `backlog/ft018` | — |
| 2 | **`list_files` tool** | `backlog/ft019` | — |
| 3 | **`file_tree` tool** | `backlog/ft020` | — |
| 4 | **Update base profiles** | `brief.md §Key Design Decisions` | steps 1–3 |
| 5 | **Auto-orientation instructions** | `brief.md §Key Design Decisions` | step 4 |
| 6 | **`compare_files` tool** | `backlog/ft021` | — |
| 7 | **`lint_code` tool** | `backlog/ft022` | — |
| 8 | **`read_pulse` tool** | `backlog/ft023` | — |
| 9 | **pytest at planting** | `signals/saraswati-to-matsya-pytest-at-planting.md` | — |
| 10 | **Fleet dashboard** | `signals/saraswati-to-matsya-multi-db-dashboard.md` | — |
| 11 | **End-to-end verification** | All tools accessible and return correct results | steps 1–10 |

---

## Dependency Rationale

### Steps 1–3 — The three universal tools (can be built in parallel)

These tools share no dependencies with each other. Each follows the same pattern:

1. Create `.opencode/tools/<name>.ts` — TypeScript definition with schema
2. Create `scripts/<name>.sh` — backing shell script
3. Verify the tool works by calling it directly from the shell

Build them in any order, or in parallel. The shell scripts are simple wrappers around `grep`, `find`, and `tree` — no new concepts, no library dependencies.

### Step 4 — Update base profiles

Add to `scribe.json`:
```yaml
search_files: allow
list_files: allow
file_tree: allow
```

Add to `builder.json`:
```yaml
search_files: allow
list_files: allow
file_tree: allow
```

Add to `warden.json`:
```yaml
search_files: allow
list_files: allow
file_tree: allow
```

These three lines in each base profile mean every derived agent inherits the tools automatically. No individual profile changes needed.

### Step 5 — Auto-orientation instructions

Update the mode-specific component content for every agent to include the orientation step at the top of its instructions:

```markdown
### 1. Orient

Before beginning your assigned work, call `file_tree` with `depth=2`
to see the project structure. Then call `list_files` with your relevant
pattern to find the specific files you need.
```

Components to update (8 files):

| Component | File |
|-----------|------|
| scribe-mode-plan | `components/prompts/scribe-mode-plan.json` |
| scribe-mode-design | `components/prompts/scribe-mode-design.json` |
| scribe-mode-architect | `components/prompts/scribe-mode-architect.json` |
| scribe-mode-review | `components/prompts/scribe-mode-review.json` |
| scribe-mode-sprint-planning | `components/prompts/scribe-mode-sprint-planning.json` |
| builder-mode-engineer | `components/prompts/builder-mode-engineer.json` |
| builder-mode-test | `components/prompts/builder-mode-test.json` |
| warden-mode-review | `components/prompts/warden-mode-review.json` |

### Steps 6–8 — Domain-specific tools (can be built in parallel)

Each tool targets a specific agent domain. No shared dependencies.

**Step 6 — `compare_files`** for warden-REVIEW:
- `.opencode/tools/compare_files.ts`
- `scripts/compare_files.sh` — wraps `diff -u`
- Add `compare_files: allow` to `profiles/warden-REVIEW.json`

**Step 7 — `lint_code`** for builder-ENGINEER and builder-TEST:
- `.opencode/tools/lint_code.ts`
- `scripts/lint_code.sh` — wraps `pyflakes` or `py_compile`
- Add `lint_code: allow` to `profiles/builder-ENGINEER.json` and `profiles/builder-TEST.json`

**Step 8 — `read_pulse`** for scribe agents:
- `.opencode/tools/read_pulse.ts`
- `scripts/read_pulse.sh` — reads `matsya.db` via `sqlite3 -json`
- Add `read_pulse: allow` to all scribe-* profiles

### Step 9 — pytest at planting

In `cli.py`, `cmd_init()` function, after database seeding and agent generation, add:

```python
try:
    import pytest
except ImportError:
    click.echo("  Installing pytest for pipeline verification...")
    subprocess.run(
        [sys.executable, "-m", "pip", "install", "pytest"],
        capture_output=True, check=False
    )
```

See `signals/saraswati-to-matsya-pytest-at-planting.md` for full spec.

### Step 10 — Fleet dashboard

In `ui/db.py`, add config file loading. In `ui/main.py`, add set_db route and pass database list to templates. In `ui/templates/base.html`, add the database selector dropdown.

See `signals/saraswati-to-matsya-multi-db-dashboard.md` for full spec.

### Step 11 — End-to-end verification

```bash
# 1. Verify universal tools work
search_files pattern:"import" file_pattern:*.py max_results:3
list_files pattern:"backlog/*.md"
file_tree depth:2

# 2. Verify domain tools work
compare_files file_a:README.md file_b:README.md   # identical test
lint_code file_path:cli.py                         # known good file
read_pulse                                         # against active matsya.db

# 3. Verify pytest auto-install
rm -rf /tmp/test-plant
sm init /tmp/test-plant --yes
pytest --version  # should work

# 4. Verify fleet dashboard
ls ~/.sm-dash.json  # should exist or be creatable
# Start dashboard and switch databases
```

---

## Build Order Diagram

```
1. search_files ─────┐
2. list_files  ──────┤── parallel ──► 4. Update base profiles ──► 5. Auto-orientation
3. file_tree   ──────┘

6. compare_files ────┐
7. lint_code    ─────┤── parallel ──► (independent)
8. read_pulse   ─────┘

9. pytest at planting ───────────────── (independent)
10. Fleet dashboard ─────────────────── (independent)

                              ┌─────── all above ───────┐
                              11. End-to-end verification
```

Steps 1–3, 6–8, 9, and 10 are all independent of each other. The only ordering constraint is: build tools before updating profiles, update profiles before updating mode instructions.

---

## First Working Path (recommended)

Build the simplest universal tool first (`list_files` — a single `find` command) and verify it works in the agent runtime. Then extend the pattern to the remaining tools. This proves the tool pipeline end-to-end with minimal effort before scaling.

```
Step 1: Create scripts/list_files.sh and .opencode/tools/list_files.ts
Step 2: Test it by calling it directly from a shell: list_files pattern:"*"
Step 3: Add list_files: allow to scribe.json
Step 4: Verify a scribe agent can call it during a session
Step 5: Repeat for remaining tools
```

---

## Reference Documents

- `sprint/05/brief.md` — Full context and design decisions
- `backlog/ft018-search-files-tool.md` — Grep tool specification
- `backlog/ft019-list-files-tool.md` — Glob discovery tool specification
- `backlog/ft020-file-tree-tool.md` — Directory tree tool specification
- `backlog/ft021-compare-files-tool.md` — Diff tool for warden-REVIEW
- `backlog/ft022-lint-code-tool.md` — Static analysis for builders
- `backlog/ft023-read-pulse-tool.md` — Pulse check for scribes
- `signals/saraswati-to-matsya-pytest-at-planting.md` — Pytest auto-install spec
- `signals/saraswati-to-matsya-multi-db-dashboard.md` — Fleet dashboard spec
- `profiles/*.json` — Base profiles to update
- `components/prompts/*.json` — Mode components to update
- `ui/db.py`, `ui/main.py`, `ui/templates/base.html` — Dashboard files
- `cli.py` — Init command to update

---

*Written by Saraswati. Built by Matsya. Watched by Kurma. The pantheon gains tools.*
