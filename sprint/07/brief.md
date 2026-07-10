# Sprint 07 — Refactor: Unify Agent Generation

*Kill the duplication. Eliminate the `<MODE_FLAG>` bug. Make `sm init` produce correct agents.*

---

## Context

During Sprint 06 profile cleanup, a bug was discovered: the `sm init` command generates agent files containing the literal string `<MODE_FLAG>` instead of the correct mode flag (e.g. `PLAN`, `ENGINEER`, `SPRINT_GATE`). The generated agents are also missing inherited base components, making them incomplete.

The root cause is duplicated agent generation logic. `cli.py` contains two separate implementations:

1. `cmd_generate_agent()` — walks the inheritance chain, substitutes `<MODE_FLAG>`, applies params (correct)
2. `cmd_init()` inline loop (lines 1163–1207) — direct component fetch only, no inheritance, no substitution (buggy)

Both paths produce the same output format (YAML frontmatter + assembled body), but the init path produces semantically incorrect output.

Sprint 07 fixes this by extracting the correct assembly logic into a shared module and making both paths use it. No new features. No new states. Just a structural refactoring that eliminates the bug at its root.

---

## The Shape of the Work

| Step | Feature | What |
|------|---------|------|
| 1 | **ft030** | Extract 6 helper functions from `cli.py` into `src/genesis_sm/generator.py`. Remove leading underscores — they become public. Update call sites in `cli.py`. |
| 2 | **ft031** | Replace the inline agent generation block in `cmd_init()` with calls to `generator.py`. Delete the duplicated ~45 lines. |
| 3 | **ft032** | Write a test script that verifies `sm init` produces correct agent files (no `<MODE_FLAG>`, full inheritance, identical to `sm generate agents` output). |

---

## Design Decisions

### Public module, not private helpers

The six functions being extracted lose their leading underscores. They were originally private to `cli.py` because they were only called from `cmd_generate_agent()`. Now that `cmd_init()` also needs them, they become public in `generator.py`. This is a natural boundary — the module name `generator` communicates their purpose.

### No behavioural changes to `sm generate agent`

The refactoring must be a pure extraction. `sm generate agent` and `sm generate agents` must produce bit-identical output before and after. The new `generator.py` functions are copies of the existing logic; no logic changes are permitted in ft030.

### One implementation, two callers

After ft031, `cmd_init()` and `cmd_generate_agent()` both call `assemble_components()` from `generator.py`. There is exactly one implementation of the assembly algorithm. The bug cannot reappear unless someone writes a third path.

---

## Existing Code That Must Not Break

- `sm generate agent <name>` — output must be identical before and after ft030
- `sm generate agents` — output must be identical
- `sm profile variant` — calls `cmd_generate_agent`, must remain correct
- All other CLI commands (`seed`, `run`, `list`, `log`, `sprint`, `status`, `profile export/import`) — unchanged

---

## Files the Engineer Should Read First

| File | Why |
|------|-----|
| `backlog/ft030-extract-agent-generator.md` | Primary feature — the extraction spec |
| `backlog/ft031-fix-init-agent-generation.md` | Secondary feature — fix the init path |
| `backlog/ft032-verify-init-generation.md` | Test and verification |
| `src/genesis_sm/cli.py` (lines 502–718, 1163–1207) | The two code paths that must be unified |
| `components/rules/bootstrap-protocol.json` | The component that contains `<MODE_FLAG>` as a template placeholder |
| `sprint/05/test-results.md` | Existing test suite — shows what was tested (and what was missed) |

---

## Deferred to Sprint 08+

- Nothing. This sprint closes a bug from Sprint 05. No new backlog items are created.

---

*Written by Saraswati. Built by Matsya. Watched by Kurma. The duplication dies here.*
