# Sprint 01 — Features

*Six features, ordered by dependency. Build in this sequence.*

---

| # | File | Feature | Depends on |
|---|------|---------|------------|
| 1 | `ft001-seed-decomposition.md` | Seed & Component Decomposition | — |
| 2 | `ft002-cli-framework.md` | CLI Framework (`sm.py`) | ft001 |
| 3 | `ft004-list-commands.md` | List Commands (`sm list profiles`, `sm list components`) | ft001, ft002 |
| 4 | `ft003-run-command.md` | Run Command (`sm run --profile`) | ft001, ft002 |
| 5 | `ft005-status-command.md` | Status Command (`sm status`) | ft003 (needs state from running) |
| 6 | `ft006-generate-agent.md` | Generate Agent (`sm generate agent`) | ft001, ft002 |
| 7 | `ft007-check-syntax-tool.md` | Check Syntax Tool (`check_syntax`) | ft001, ft006 |

---

## Dependency rationale

**ft001** is the foundation — without the seed data in the database, nothing else has anything to work with.

**ft002** provides the command routing — all other features use `sm <command>` dispatch.

**ft004** can be built as soon as ft001 and ft002 exist, since it's just queries. It also serves as a verification that seeding worked correctly.

**ft003** requires the profile data and the CLI framework, plus minor refactoring of `state_machine.py` to be importable as a module.

**ft005** depends on the run command producing state that can be queried.

**ft006** is the capstone — it consumes everything built before it to produce the final artifact (OpenCode agent files).

**ft007** is the narrowest feature — a single-purpose tool for syntax verification. It depends on ft001 (the Builder profile must exist in seed data) and ft006 (the generated agent template must include the tool permission). It can be built at any point after ft001+ft006, but is placed last because it modifies an existing profile rather than creating new infrastructure.

---

## Reference document

See `roles_example_opt.md` in the project root for the complete reference map of the component-decomposed profile data. This is the target state that ft001 should produce.
