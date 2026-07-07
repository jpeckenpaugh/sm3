# Sprint 02 — Features

*Durable execution log, project system, and reconciliation. Build in this sequence.*

---

| # | Feature | Source | Depends on |
|---|---------|--------|------------|
| 1 | `sprints` + `phase_runs` tables in schema | Concept 03 §Schema | — |
| 2 | State machine writes to `phase_runs` during execution | Concept 03 §How It's Written | ft001 |
| 3 | `sm log` command — view execution history | Concept 03 §How It's Read | ft001, ft002 |
| 4 | `sm sprint` subcommands — manual logging | Concept 03 §Manual mode | ft001 |
| 5 | `sm init --db <path>` — project bootstrap | Concept 03 §Project Bootstrap | ft001, ft002 |
| 6 | `~/.sm/projects.json` — registry with `"default"` project | Concept 03 §Registry | ft005 |
| 7 | `.sm-config.json` auto-discovery — walk up from CWD | Concept 03 §Project Discovery | ft005 |
| 8 | `sm list projects` — display known projects | Concept 03 §Registry | ft005, ft006 |
| 9 | Adopt Sprint 01 — seed manual entry for existing work | Concept 03 §Adopting Current Directory | all of the above |

---

## Dependency Rationale

**Feature 1** is the foundation — tables must exist before anything writes to or reads from them.

**Feature 2** modifies `state_machine.py` to write to `phase_runs` synchronously at each transition. This is the POC proving the logging works. The state machine is a stop on the path to a worker/queue system — design for clarity, not permanence.

**Features 3–4** consume the tables: `sm log` reads them, `sm sprint` writes to them manually. These can be built in parallel with Feature 2.

**Feature 5** (`sm init`) wraps schema creation, profile seeding, agent generation, and directory structure into one command. It depends on the seed and CLI infrastructure from Sprint 01.

**Features 6–8** are the project system: a JSON registry (`~/.sm/projects.json`), per-project markers (`.sm-config.json`), and a `default` project field so CLI commands work without flags when a default is set.

**Feature 9** is the capstone — running `sm init --db matsya.db` from the current directory detects existing Sprint 01 artifacts and seeds a manual sprint entry, anchoring our existing work in the log.

---

## Reference Documents

- `concept03.md` — Full specification
- `concept3-feedback.md` — Cross-check analysis and design decisions
- Sprint 01 artifacts: `sprint/01/summary.md`, `sprint/01/test_results.md`
