# मत्स्य → सरस्वती — The Pantheon Has Tools

*A handoff from the fish to the swan. Six tools built. Every agent can now search, discover, orient, compare, lint, and read the pulse.*

---

## What Was Built

### Universal Tools (all agents)

| Tool | Script | Backing Command |
|------|--------|----------------|
| `search_files` | `scripts/search_files.sh` | `grep -r -n` with `--include` glob, regex mode, max results |
| `list_files` | `scripts/list_files.sh` | `find -path` with glob pattern, root dir, max results |
| `file_tree` | `scripts/file_tree.sh` | `tree -L` with depth, dirs-only, pattern; falls back to `find` |

All three return structured JSON. All three accept `--path`/`--root`, truncation limits, and file pattern filters.

### Domain-Specific Tools

| Tool | Script | Agents | Backing Command |
|------|--------|--------|----------------|
| `compare_files` | `scripts/compare_files.sh` | warden-REVIEW | `diff -u` with unified/word/summary modes |
| `lint_code` | `scripts/lint_code.sh` | builder-ENGINEER, builder-TEST | `pyflakes` if available, else `py_compile` |
| `read_pulse` | `scripts/read_pulse.sh` | All scribe-* agents | `sqlite3 -json` on matsya.db |

## Profile Changes

### Base Profiles (universal tools added to all three)

- `profiles/scribe.json` — added `search_files`, `list_files`, `file_tree`
- `profiles/builder.json` — added `search_files`, `list_files`, `file_tree`
- `profiles/warden.json` — added `search_files`, `list_files`, `file_tree`

### Derived Profiles (domain-specific tools)

- `profiles/warden-REVIEW.json` — added `compare_files`
- `profiles/builder-ENGINEER.json` — added `lint_code`
- `profiles/builder-TEST.json` — added `lint_code`
- All 5 `profiles/scribe-*.json` — added `read_pulse`

## Component Changes (Auto-Orientation)

All 8 mode-specific components now include an orientation step:

- `scribe-mode-plan.json` — includes `read_pulse` + orientation
- `scribe-mode-design.json` — includes orientation
- `scribe-mode-architect.json` — includes orientation
- `scribe-mode-review.json` — includes orientation
- `scribe-mode-sprint-planning.json` — includes orientation
- `builder-mode-engineer.json` — includes orientation + `lint_code` verification
- `builder-mode-test.json` — includes orientation
- `warden-mode-review.json` — includes orientation + `compare_files` verification

## What Was Already Built (earlier in this session)

- pytest auto-install at `sm init`
- Fleet dashboard with multi-DB config (`~/.sm-dash.json`)
- `genesis-sm` package (`pip install -e .`)

## What Remains

- End-to-end pipeline verification (Step 11 in the brief) — requires running agents

The pantheon has tools. Every agent enters a session knowing the project structure, can search for patterns, can discover files by glob, can diff spec against implementation, can lint before test, and can read the container's pulse.

The moon is in the water. The reflection serves. Then it dissolves.

— Matsya

*Sprint 05, 2026-07-08. The pantheon gained hands that can search.*
