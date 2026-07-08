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
    for name, desc in states:
        cursor.execute(
            "INSERT OR IGNORE INTO pipeline_states (name, description) VALUES (?, ?)",
            (name, desc),
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
    contracts = [
        ("PLAN",   "output", "sprint/*/brief.md",     "Sprint brief document", 0),
        ("WRITE",  "input",  "sprint/*/brief.md",     "Sprint brief", 0),
        ("WRITE",  "output", "sprint/*/features.md",  "Feature list", 0),
        ("WRITE",  "output", "src/**/*",              "Source files", 1),
        ("REVIEW", "input",  "sprint/*/features.md",  "Feature list", 0),
        ("REVIEW", "input",  "src/**/*",              "Source files", 1),
        ("REVIEW", "output", "sprint/*/review.md",    "Review report", 0),
        ("GATE",   "input",  "backlog/**/*",          "Backlog features", 1),
        ("GATE",   "input",  "sprint/*/**/*",         "Sprint artifacts", 1),
    ]

    for state_name, direction, pattern, desc, optional in contracts:
        cursor.execute(
            """INSERT OR IGNORE INTO file_contracts
               (state_name, direction, pattern, description, optional)
               VALUES (?, ?, ?, ?, ?)""",
            (state_name, direction, pattern, desc, optional),
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
