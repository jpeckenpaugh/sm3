# Saraswati → Matsya Handoff

## CREATE TABLE Statements

```sql
CREATE TABLE IF NOT EXISTS profiles (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    name        TEXT    NOT NULL UNIQUE,
    version     TEXT    NOT NULL DEFAULT '0.1.0',
    header      TEXT    DEFAULT '{}',       -- JSON
    permissions TEXT    DEFAULT '{}',       -- JSON
    preamble    TEXT    DEFAULT '',
    body        TEXT    DEFAULT '',
    created_at  TEXT    NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%SZ', 'now')),
    updated_at  TEXT    NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%SZ', 'now'))
);

CREATE TABLE IF NOT EXISTS components (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    type        TEXT    NOT NULL,           -- 'tool' | 'prompt' | 'rule'
    name        TEXT    NOT NULL,
    content     TEXT    NOT NULL DEFAULT '', -- JSON or markdown
    created_at  TEXT    NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%SZ', 'now')),
    UNIQUE(type, name)
);

CREATE TABLE IF NOT EXISTS profile_components (
    id           INTEGER PRIMARY KEY AUTOINCREMENT,
    profile_id   INTEGER NOT NULL REFERENCES profiles(id) ON DELETE CASCADE,
    component_id INTEGER NOT NULL REFERENCES components(id) ON DELETE CASCADE,
    order_idx    INTEGER NOT NULL DEFAULT 0,
    params       TEXT    DEFAULT '{}',      -- JSON overrides
    UNIQUE(profile_id, component_id)
);
```

## State Machine Loop Pseudocode

```
state_machine:
  phases: [PLAN, WRITE, REVIEW, COMMIT, GATE]

  for each iteration (num from 1 to N):
    for each phase:
      attempt = 0
      while attempt < max_retries:
        run phase script
        if success: break
        attempt += 1
      if attempt == max_retries:
        fail iteration

  GATE phase:
    if backlog non-empty:
      num += 1; goto PLAN
    else:
      SHIP / wait for Vasuki signal
```

Current implementation (`state_machine.py`) hardcodes 5 iterations, 0.4 probability, 4 retries. This should become config-driven.

## git_commit.sh Spec

A script that:
1. Stages all changes (`git add -A`)
2. Reads a commit message from a file or stdin
3. Runs `git commit -m <message>`
4. Exits 0 on success, non-zero on failure

Optional features for later:
- GPG signing
- Conventional commit enforcement
- Branch validation (no commits to main without PR)

## Unresolved Open Questions

1. **Component versioning**: Should `components.content` be a separate versioned table?
2. **Sprint meta**: How does `is_meta` relate to profiles — are meta-profiles just profiles with a flag?
3. **Inheritance**: Should profile extension (`extends`) be stored inline (JSON) or as a FK link?
4. **Gate signal**: What exactly is Vasuki's signal — a file touch, a webhook, a DB poll?
5. **Probability**: Is 0.4 a permanent default or should it be per-phase configurable?

## Files Delivered

| File | Purpose |
|------|---------|
| `schema.sql.md` | SQL schema documentation |
| `state_machine.py` | Python state machine (5 iterations, 0.4 prob, 4 retries) |
| `wait-and-touch.sh` | Sleep + probabilistic file touch |
| `reflection-for-kurma.md` | Reflection for the Hypervisor |
| `saraswati-to-matsya.md` | This handoff |
