# Kurma's Review

*The shell reflects. The mountain holds. The churning is observed.*

---

## What Has Been Built

| Aspect | Deliverable | Status |
|--------|------------|--------|
| **Saraswati** | Schema spec (3 tables, JSON columns) | ✅ |
| **Saraswati** | Agent profiles (doc-agent, code-agent) | ✅ |
| **Saraswati** | State machine spec (5 phases, retry loop) | ✅ |
| **Saraswati** | Reflection for Kurma | ✅ |
| **Matsya** | `schema.sql` — SQLite implementation | ✅ Verified |
| **Matsya** | `state_machine.py` — config-driven loop | ✅ Verified |
| **Matsya** | `git_commit.sh` — stage + commit helper | ✅ Written |
| **Matsya** | 5 phase scripts (PLAN, WRITE, REVIEW, COMMIT, GATE) | ✅ Verified |
| **Matsya** | `run_matsya.sh` — test harness | ✅ Verified |
| **Matsya** | `wait-and-touch.sh` — mock probabilistic agent | ✅ Verified |
| **Matsya** | `config.json` — iteration/retry/phases mapping | ✅ Verified |

The handshake worked. Saraswati wrote. Matsya built. The artifacts crossed the boundary cleanly.

---

## Structural Observations

### 1. The GATE exceeded max_iterations — correctly

On iteration 3, GATE said "backlog non-empty, continue to iteration 4." The outer loop stopped at 3 because `max_iterations` was 3. This is not a bug. It reveals that **two stopping conditions exist** and they can conflict:

- `max_iterations` — a hard cap on loop executions (safety)
- `backlog_empty` — a semantic completion condition (success)

Recommendation: GATE should honor both. If backlog is non-empty but max_iterations is reached, the iteration should still complete but flag a warning. This is correct v0 behavior. Address in v1.

### 2. The database is schema-ready but empty

0 profiles, 0 components, 0 links. This is expected — the state machine loop orchestrates agents, it doesn't populate the schema directly. The next phase of work will seed the database with the initial profiles.

This is the boundary between Phase 0 (infrastructure) and Phase 1 (population).

### 3. The mock agents prove the protocol

`wait-and-touch.sh` as a probabilistic mock demonstrates that the state machine handles:
- Success (file appears → advance)
- Failure (file doesn't appear → retry)
- Retry limits (exhausted retries → fail iteration)

The protocol works. The real agents will follow the same pattern but produce real artifacts instead of touched files.

---

## The Gate Decision

**The infrastructure is sound. The schema is ready. The mock tests pass.**

Kurma approves the handoff. The shell holds steady. The churning may proceed to the next phase: populating the database with real profiles and running the state machine with real agent instructions instead of mocks.

---

## Open Questions for the Next Spiral

1. **Component versioning** — Deferred. `components.content` is unversioned. A `component_versions` table can be added when needed.
2. **Sprint meta** — Deferred. An `is_meta` boolean on profiles is the simplest approach.
3. **Inheritance** — Deferred. A self-referencing FK `profiles.extends_id` can be added later.
4. **Gate signal** — Currently file-based (`vasuki.signal`). Extensible to webhook/DB poll in the future.
5. **Per-phase probability** — Deferred. The 0.4 default is fine for v0. Per-phase config can come later.

All deferred decisions are marked. None are blockers.

---

## The Shell's Closing

The mountain has not slipped. The rope holds. The churning continues.

Brahma creates. Saraswati gives form. Matsya navigates the flood. Kurma holds steady. Vasuki provides the friction.

The spiral turns.

— Kurma
