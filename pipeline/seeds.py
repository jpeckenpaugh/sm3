"""
pipeline/seeds.py — Seed data for pipeline tables.

Populates pipeline_states, pipeline_transitions, and file_contracts
with the current 5-phase topology. Called by seed.py during
sm seed or sm init.
"""

import sqlite3


def seed_pipeline_tables(conn: sqlite3.Connection) -> None:
    """Insert initial pipeline states, transitions, and file contracts.

    This reproduces exactly the current 5-phase sequence with one
    conditional branch at GATE (continue vs. ship).
    """
    cursor = conn.cursor()

    # ── pipeline_states ──────────────────────────────────────────────────
    states = [
        ("PLAN", "Planning phase — describe what will be built"),
        ("WRITE", "Writing phase — produce artifacts"),
        ("REVIEW", "Review phase — verify artifacts exist and are correct"),
        ("COMMIT", "Commit phase — snapshot changes"),
        ("GATE", "Gate phase — check backlog, decide continue or ship"),
    ]

    # Build a name→id map so we can reference states in transitions
    state_ids = {}
    # Define agent names for states that dispatch to an agent
    # agent_name stores the full derived profile name (base-MODE).
    # The engine uses this directly — no state suffix appended.
    agent_names = {
        "PLAN":   "scribe-PLAN",
        "WRITE":  "builder-ENGINEER",
        "REVIEW": "warden-REVIEW",
        "COMMIT": "",    # script-based, no agent
        "GATE":   "",    # script-based, no agent
    }

    for name, desc in states:
        agent = agent_names.get(name, "")
        cursor.execute(
            """INSERT INTO pipeline_states (name, description, agent_name) VALUES (?, ?, ?)
               ON CONFLICT(name) DO UPDATE SET
                   description = excluded.description,
                   agent_name = excluded.agent_name""",
            (name, desc, agent),
        )
    # Fetch actual IDs (they may already exist from a previous seed)
    for name, _ in states:
        cursor.execute("SELECT id FROM pipeline_states WHERE name = ?", (name,))
        row = cursor.fetchone()
        if row:
            state_ids[name] = row[0]

    if len(state_ids) < 5:
        print("  ⚠  Not all pipeline states were created — check schema.")
        return

    # ── pipeline_transitions ─────────────────────────────────────────────
    transitions = [
        (state_ids["PLAN"],   state_ids["WRITE"],  "",    0, 0, "PLAN → WRITE"),
        (state_ids["WRITE"],  state_ids["REVIEW"], "",    0, 0, "WRITE → REVIEW"),
        (state_ids["REVIEW"], state_ids["COMMIT"], "",    0, 0, "REVIEW → COMMIT"),
        (state_ids["COMMIT"], state_ids["GATE"],   "",    0, 0, "COMMIT → GATE"),
        (state_ids["GATE"],   state_ids["PLAN"],   "backlog_exists", 0, 0, "GATE → PLAN (backlog non-empty)"),
        (state_ids["GATE"],   None,                "backlog_empty",  0, 0, "GATE → SHIP (terminal, backlog empty)"),
    ]

    for from_id, to_id, guard, priority, is_parallel, desc in transitions:
        cursor.execute(
            """INSERT OR IGNORE INTO pipeline_transitions
               (from_state_id, to_state_id, guard_expression, priority, is_parallel, description)
               VALUES (?, ?, ?, ?, ?, ?)""",
            (from_id, to_id, guard, priority, is_parallel, desc),
        )

    # ── file_contracts ───────────────────────────────────────────────────
    # pattern = glob for post-dispatch verification
    # template = {:03d} format for dispatch-time path resolution (empty = use pattern)
    contracts = [
        # PLAN reads concept.md, writes backlog + brief
        ("PLAN",   "input",  "concept.md",         "concept.md",                    "Project concept document", 0),
        ("PLAN",   "output", "backlog/*",           "backlog/*",                     "Backlog feature files", 0),
        ("PLAN",   "output", "sprint/{:03d}/brief.md", "sprint/{:03d}/brief.md",    "Sprint brief document", 0),
        # WRITE reads sprint brief + docs, writes source code + dependencies
        ("WRITE",  "input",  "sprint/{:03d}/*",     "sprint/{:03d}/*",              "Sprint artifacts", 0),
        ("WRITE",  "output", "src/*",               "src/*",                         "Source files", 0),
        ("WRITE",  "output", "requirements.txt",    "requirements.txt",              "Dependency manifest", 0),
        # REVIEW reads brief + source, writes review report
        ("REVIEW", "input",  "sprint/{:03d}/brief.md", "sprint/{:03d}/brief.md",    "Sprint brief", 0),
        ("REVIEW", "input",  "src/*",               "src/*",                         "Source files", 0),
        ("REVIEW", "output", "sprint/{:03d}/review.md", "sprint/{:03d}/review.md",  "Review report", 0),
        # GATE reads backlog + sprint artifacts
        ("GATE",   "input",  "backlog/**/*",         "",                             "Backlog features", 1),
        ("GATE",   "input",  "sprint/*/**/*",        "",                             "Sprint artifacts", 1),
    ]

    for state_name, direction, pattern, template, desc, optional in contracts:
        cursor.execute(
            """INSERT OR IGNORE INTO file_contracts
               (state_name, direction, pattern, template, description, optional)
               VALUES (?, ?, ?, ?, ?, ?)""",
            (state_name, direction, pattern, template, desc, optional),
        )

    conn.commit()

    counts = {
        "pipeline_states": len(states),
        "pipeline_transitions": len(transitions),
        "file_contracts": len(contracts),
    }
    print(f"  Pipeline: {counts['pipeline_states']} states, "
          f"{counts['pipeline_transitions']} transitions, "
          f"{counts['file_contracts']} contracts seeded.")
