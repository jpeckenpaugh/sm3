# Concept 02 — Seed & CLI Toolchain

*A Warden's directive for the Scribe and Builder.*  
*The next small thing that makes the experiment more reproducible.*

---

## The Goal

Three deliverables, in order, that let us drive the state machine from seeded profiles without requiring a human to manually load data or a non-deterministic agent session to maintain SQLite rows by hand.

---

## 1. Profile Seed Data

A `profiles/` directory containing six JSON files — one per base class:

| File | Profile Name |
|------|-------------|
| `profiles/scribe.json` | scribe |
| `profiles/builder.json` | builder |
| `profiles/warden.json` | warden |
| `profiles/origin.json` | origin |
| `profiles/courier.json` | courier |
| `profiles/keeper.json` | keeper |

Each JSON file matches the existing `profiles` table schema (name, version, header, permissions, preamble, body). One file per profile, not one giant file.

---

## 2. Seeder Script

A single Python script (`seed.py`) that:

- Reads all `profiles/*.json` files
- Connects to the SQLite database (path configurable, default `./state_machine.db`)
- Upserts each profile into the `profiles` table (match on `name`, update if newer version exists)
- Is idempotent — safe to re-run multiple times
- Exits 0 on success, non-zero with clear error on failure
- Python standard library only — no external dependencies

---

## 3. CLI Entry Point

A Python script (`sm.py`) that wraps the existing state machine:

```
sm seed                    # run the seeder
sm run --profile <name>    # select profile from DB, feed into state machine loop
sm list profiles           # query and display profiles
sm list components         # query and display components
sm status                  # show current sprint/phase state
```

The existing `state_machine.py` should be importable as a module, not called via subprocess.

---

## Constraints

- Python standard library only. No pip install required.
- SQLite via `sqlite3` (already in the project).
- JSON for profile data (not YAML — fewer dependencies).
- The seeder and CLI should work on a fresh clone with just `python seed.py` and `python sm.py`.

---

## Known Gaps (Deferred)

- The database does not yet track sprint/iteration state. That will come in a future concept.
- Components and profile_components tables exist but are not populated by this seed.
- No web UI — that comes after the CLI is proven.

---

*Written by the Warden, for the Scribe to specify and the Builder to implement.*  
*Kurma holds. Vasuki signals. The spiral turns.*
