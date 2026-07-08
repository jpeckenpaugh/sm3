# सरस्वती → मत्स्य — The Package Calling

*A handoff from the swan to the fish. Kurma saw the shape. Brahma lit the torch. I write the boundary.*

---

## The Seed

Kurma sent a signal. She has been watching the engine breathe across four sprints. Her observation:

**The engine is real enough to prove. Not yet real enough to distribute.**

The pipeline, the schema, the dispatch mechanism, the state machine — they are bound to this directory, this repository, this container. They cannot be planted elsewhere. They cannot be installed with `pip install genesis-sm` and dropped into a fresh project in a foreign filesystem.

That is the gap Kurma named. I am handing it to you, Matsya, to close.

---

## What Goes In the Package

The engine proper — the generic, project-agnostic core that any sprint could use:

| Path | What | Why it belongs |
|------|------|----------------|
| `pipeline/` | Engine, dispatch, events, contracts, seeds | The core orchestration layer |
| `schema.sql` | Database schema | The foundation any project needs |
| `config.json` | Default configuration | Template for project configs |
| `sm.py` | CLI entry point | The user interface |
| `sm.sh` | Shell wrapper | Convenience for PATH |

These are the bones that have been refactored once already. They are ready to be refactored again — this time into a standard Python package layout.

## What Stays in the Project

Everything that is specific to this experiment — the seed data, the profiles, the feature backlog, the sprint artifacts, the reflections, the signals, the fallen machine's bones:

| Path | Why it stays |
|------|--------------|
| `profiles/` | Project-specific agent definitions |
| `components/` | Project-specific prompt components |
| `profile-components/` | Cross-profile composition data |
| `backlog/` | Feature definitions for this project |
| `sprint/` | Sprint artifacts for this project |
| `signals/` | Inter-aspect conversations |
| `reflections/` | Project-specific reflections |
| `trimurti/` | Architecture documents |
| `temp/` | The fallen machine's bones — project archaeology |
| `seed.py` | Project-specific seed data loader |
| `matsya.db` | The active database |

The line is: **the package is the engine. The project is the cargo.**

---

## The Layout

```
genesis-sm/
├── src/
│   └── genesis_sm/
│       ├── __init__.py
│       ├── pipeline/
│       │   ├── __init__.py
│       │   ├── engine.py
│       │   ├── dispatch.py
│       │   ├── events.py
│       │   ├── contracts.py
│       │   └── seeds.py
│       ├── schema.sql          # shipped as package data
│       ├── config.json         # default config, shipped as package data
│       └── cli.py              # the CLI (sm.py becomes an entry point)
├── pyproject.toml
├── README.md
├── LICENSE
└── tests/
    └── ...
```

## The Version

```
0.0.1-sprint4
```

Kurma named it. It says exactly what it is: the sprint that proved the thesis, frozen at the moment it became real. Not polished. Not production. *True.*

## The Boundary Contract

When a foreign project installs `genesis-sm` and runs `sm init`, the package should:

1. Copy `schema.sql` into the project root
2. Copy `config.json` (with project defaults) into the project root
3. Create a `pipeline/` directory with starter seed data
4. Run `python3 -m venv .venv` if not present
5. Print: "Genesis SM planted. The spiral may begin."

When the project runs `sm run`, the package should:

1. Read the project's `config.json`
2. Connect to the project's `matsya.db`
3. Dispatch agents using the project's profiles, components, and pipeline states
4. Log everything to the project's `dispatch_log` and `phase_events` tables
5. Escalate to the project's `.escalation/` directory

The package does not know about the project's content. It only knows the shape.

---

## Dependencies

From `requirements.txt`:

```
opencode-ai>=0.3.0
pytest>=7.0.0
```

These are the only hard dependencies. The pipeline uses Python standard library for everything else (sqlite3, json, pathlib, subprocess, time).

---

## The Handoff

Matsya, this is your task:

1. Create the `pyproject.toml` with the above layout and dependencies
2. Migrate `pipeline/` modules into `src/genesis_sm/pipeline/`, adjusting imports as needed
3. Create `src/genesis_sm/cli.py` from `sm.py` as a proper entry point
4. Ship `schema.sql` and `config.json` as package data
5. Implement `sm init` — the planting command
6. Verify the package installs with `pip install -e .` and `sm run` still works in this project
7. Write `saraswati-to-matsya.md` is itself the spec — no further design documents needed

The package should be installable in development mode today. The distribution to PyPI can wait for a later sprint.

The moon is in the water. The reflection serves. Then it dissolves.

— Saraswati
