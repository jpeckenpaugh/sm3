# Concept 01 — The Genesis Container

*A handoff from the Hypervisor to the first agent team.*  
*This document defines Sprint 0, Phase 0: the seed.*

---

## The Vision

A mostly-empty Docker container is fired up with a few lines of code. Inside it runs one agent — the Hypervisor — who spawns two below them, who spawn five below that, and together they build an enterprise-grade state machine that builds itself from the inside out.

The state machine's output is a running web application: SQLite database, FastAPI with Pydantic models and validation, and a lightweight Bootstrap CSS/JS frontend. The Origin opens a browser and sees a bird's-eye view of everything the system is doing.

But that sprint comes later. This is Sprint 0, Phase 0: **the seed that makes the rest possible.**

---

## The Seed

Sprint 0 Phase 0 produces exactly **three things**:

### 1. A SQLite Database Schema

A single database that stores:
- **Agent profiles** — the YAML definitions that bound each agent's role
- **Profile components** — reusable atoms (permission sets, boundary statements, mode flags) that profiles are assembled from
- **State machine definitions** — the phases, transitions, and gate conditions that define each sprint

The schema should be flexible enough to evolve without migrations. JSON columns for anything that might change shape. Strings for everything else.

### 2. Two Agent Profiles

The two roles that will build everything after this phase:

**doc-agent.md** — writes only .md files. Does exactly what it's told. The voice of the framework.
```yaml
description: Write docs only.
mode: all
temperature: 0.1
permission:
  "*": deny
  edit: { "*.md": allow }
---
You do exactly as you are told. No more, and no less.
```

**code-agent.md** — writes code by writing .md files with code blocks. Same permission boundary. Same grounding axiom. Four sub-roles it can occupy:
- ENGINEER — builds features per plan.md and spec.md
- TEST — writes tests and produces test artifacts
- DEVOPS — validates with tests, finalizes requirements.txt, provides install.sh and start.sh
- PM — wears all hats, moves the sprint forward, documents new features in backlog

```yaml
description: Write docs only.
mode: all
temperature: 0.1
permission:
  "*": deny
  edit: { "*.md": allow }
---
You do exactly as you are told. No more, and no less. Any given turn, you will occupy only 1 role, with strict separation of concerns.
ENGINEER will do their best to build the features in the current sprint, follow the plan.md and use the spec.md as written.
TEST will write tests and produce the artifacts they are required to.
DEVOPS will use the tests to verify and refine code, finalizing requirements.txt and providing install.sh and start.sh for validation.
PM as the Project Manager must wear all hats and do what is required to move the sprint forward to its completion, and document new features in the backlog as they arise.
```

### 3. A State Machine Specification

The phases that define every sprint. Each phase follows the same pattern:

```
ACTION → VERIFY → COMMIT (or ROLLBACK)
```

The machine states:

| Phase | Action | Agent | Verifies |
|-------|--------|-------|----------|
| BACKLOG | Populate `backlog/` with feature files | doc-agent | Files exist |
| BRIEF | Append technical briefs to feature files | doc-agent | Briefs appended |
| PLAN | Move features to `sprint/{N}/`, write plan.md | doc-agent | plan.md exists |
| ARCHITECT | Write spec.md for the sprint | doc-agent | spec.md exists |
| ENGINEER | Produce outputs in `src/*` | code-agent (ENGINEER) | src/ populated |
| TEST | Create tests in `sprint/{N}/test/*`, generate report.md | code-agent (TEST) | report.md exists |
| DEVOPS | Generate requirements.txt, install.sh, start.sh, recommendation.md | code-agent (DEVOPS) | Artifacts exist |
| PM | Resolve blockers, update backlog, write README if backlog empty | code-agent (PM) | No blockers |
| GATE | If backlog empty → SHIP. Else increment N → PLAN | Hypervisor | Backlog checked |
| SHIP | Sprint complete. Framework outputs are final. | — | — |

Every phase begins with a git commit checkpoint before action, and ends with a git commit if VERIFY passes. If VERIFY fails, rollback to the pre-action commit.

---

## The Contract

The agent who receives this document will:

1. **Create the SQLite schema** (one table or many — the Steward does not prescribe)
2. **Write doc-agent.md and code-agent.md** to disk
3. **Write the state machine loop** in Python — minimal, ~50-100 lines — that reads the schema, dispatches to the right agent profile, verifies, and advances
4. **Commit everything** with message "Sprint 0, Phase 0: seed planted"

The seed is now planted. The system can water itself.

---

## Open Questions for the First Agent

- Should profiles be stored in the DB or on disk as .md files? Both? The DB gives the web UI something to query. Files give git something to track.
- The state machine loop — inline in the profile table as a JSON state graph, or hardcoded in Python? Hardcoded is simpler. JSON is more flexible for the UI.
- What's the git_commit.sh helper? A one-liner or an agent call?

Answer these as you see fit. You have authority over the implementation. The Hypervisor will review after first commit.

---

*This document was written by the Steward at the direction of the Hypervisor.*  
*It represents Sprint 0, Phase 0 of the Genesis Container experiment.*  
*The spiral turns.*
