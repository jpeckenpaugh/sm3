"""
genesis_sm.pipeline.seeds — Seed data for pipeline tables.

Populates pipeline_states, pipeline_transitions, and file_contracts
with the expanded 9-state pipeline from Saraswati's canon.

See signals/saraswati-to-matsya-the-expanded-pantheon.md for the full spec.

Migrated from the project root (pipeline/seeds.py) into the genesis-sm
package in Sprint 05.
"""

import sqlite3


def seed_pipeline_tables(conn: sqlite3.Connection) -> None:
    """Insert the full pipeline: 10 states, 10 transitions, 25 contracts."""
    cursor = conn.cursor()

    # ── pipeline_states ──────────────────────────────────────────────────
    # Saraswati's expanded pantheon: 10 states, 3 base profiles, 7 derived agents
    states = [
        ("POPULATE_BACKLOG", "Read concept, decompose into backlog features", "scribe-POPULATE_BACKLOG"),
        ("SPRINT_PLANNING",  "Select features for this sprint, write plan",   "scribe-SPRINT_PLANNING"),
        ("DESIGN",           "Write feature design document",                "scribe-DESIGN"),
        ("ARCHITECT",        "Write technical specification",               "scribe-ARCHITECT"),
        ("ENGINEER",         "Implement code from specification",           "builder-ENGINEER"),
        ("TEST",             "Build and run tests from spec and code",       "builder-TEST"),
        ("LEAD",             "Resolve blockers, polish code, create devops", "builder-LEAD"),
        ("REVIEW",           "Read spec, code, test report, write review",  "scribe-REVIEW"),
        ("SPRINT_GATE",      "Check backlog, evaluate gates, decide",       "warden-GATE"),
        ("COMMIT",           "Git commit — script, no agent",               ""),
    ]

    for name, desc, agent in states:
        cursor.execute(
            """INSERT INTO pipeline_states (name, description, agent_name) VALUES (?, ?, ?)
               ON CONFLICT(name) DO UPDATE SET
                   description = excluded.description,
                   agent_name = excluded.agent_name""",
            (name, desc, agent),
        )

    state_ids = {}
    for name, _, _ in states:
        cursor.execute("SELECT id FROM pipeline_states WHERE name = ?", (name,))
        row = cursor.fetchone()
        if row:
            state_ids[name] = row[0]

    # ── pipeline_transitions ─────────────────────────────────────────────
    # Linear with one conditional branch at SPRINT_GATE
    transitions = [
        (state_ids["POPULATE_BACKLOG"], state_ids["SPRINT_PLANNING"], "",   0, "POPULATE_BACKLOG → SPRINT_PLANNING"),
        (state_ids["SPRINT_PLANNING"],  state_ids["DESIGN"],          "",   0, "SPRINT_PLANNING → DESIGN"),
        (state_ids["DESIGN"],           state_ids["ARCHITECT"],       "",   0, "DESIGN → ARCHITECT"),
        (state_ids["ARCHITECT"],        state_ids["ENGINEER"],     "",     0, "ARCHITECT → ENGINEER"),
        (state_ids["ENGINEER"],         state_ids["TEST"],   "",     0, "ENGINEER → TEST"),
        (state_ids["TEST"],             state_ids["LEAD"], "",     0, "TEST → LEAD"),
        (state_ids["LEAD"],             state_ids["REVIEW"], "",     0, "LEAD → REVIEW"),
        (state_ids["REVIEW"],           state_ids["SPRINT_GATE"],  "",     0, "REVIEW → SPRINT_GATE"),
        (state_ids["SPRINT_GATE"],      state_ids["POPULATE_BACKLOG"], "backlog_exists", 0, "SPRINT_GATE → POPULATE_BACKLOG (backlog non-empty)"),
        (state_ids["SPRINT_GATE"],      None,                      "backlog_empty",  0, "SPRINT_GATE → (terminal, backlog empty)"),
    ]

    for from_id, to_id, guard, priority, desc in transitions:
        cursor.execute(
            """INSERT OR IGNORE INTO pipeline_transitions
               (from_state_id, to_state_id, guard_expression, priority, description)
               VALUES (?, ?, ?, ?, ?)""",
            (from_id, to_id, guard, priority, desc),
        )

    # ── file_contracts ───────────────────────────────────────────────────
    # Deduplicate before inserting (fixes duplicate rows from pre-Sprint 07 seeds)
    cursor.execute("""
        DELETE FROM file_contracts
        WHERE id NOT IN (
            SELECT MIN(id) FROM file_contracts
            GROUP BY state_name, direction, pattern
        )
    """)

    contracts = [
        ("POPULATE_BACKLOG", "input",  "concept.md",                     "concept.md",                              "Project concept document", 0),
        ("POPULATE_BACKLOG", "output", "backlog/ft-*.md",                "backlog/ft-*.md",                         "Backlog feature files", 0),
        ("SPRINT_PLANNING",  "input",  "backlog/ft-*.md",                "backlog/ft-*.md",                         "Backlog feature files", 0),
        ("SPRINT_PLANNING",  "output", "sprint/{:03d}/features/ft-*.md", "sprint/{:03d}/features/ft-*.md",          "Selected feature files", 0),
        ("SPRINT_PLANNING",  "output", "sprint/{:03d}/plan.md",          "sprint/{:03d}/plan.md",                   "Sprint plan document", 0),
        ("DESIGN",           "input",  "sprint/{:03d}/features/ft-*.md", "sprint/{:03d}/features/ft-*.md",          "Selected feature files", 0),
        ("DESIGN",           "output", "sprint/{:03d}/design.md",        "sprint/{:03d}/design.md",                 "Feature design document", 0),
        ("ARCHITECT",        "input",  "sprint/{:03d}/design.md",   "sprint/{:03d}/design.md",         "Feature design document", 0),
        ("ARCHITECT",        "output", "sprint/{:03d}/spec.md",     "sprint/{:03d}/spec.md",           "Technical specification", 0),
        ("ENGINEER",         "input",  "sprint/{:03d}/spec.md",     "sprint/{:03d}/spec.md",           "Technical specification", 0),
        ("ENGINEER",         "output", "src/**/*",                  "src/**/*",                         "Source code files", 1),
        ("ENGINEER",         "output", "requirements.txt",          "requirements.txt",                 "Dependency manifest", 1),
        ("TEST",             "input",  "sprint/{:03d}/spec.md",     "sprint/{:03d}/spec.md",           "Technical specification", 0),
        ("TEST",             "input",  "src/**/*",                  "src/**/*",                         "Source code files", 1),
        ("TEST",             "output", "tests/**/*",                "tests/**/*",                       "Executable test files", 1),
        ("TEST",             "output", "sprint/{:03d}/test-report.md", "sprint/{:03d}/test-report.md", "Test results report", 0),
        ("LEAD",             "input",  "sprint/{:03d}/spec.md",     "sprint/{:03d}/spec.md",           "Technical specification", 0),
        ("LEAD",             "input",  "src/**/*",                  "src/**/*",                         "Source code files", 1),
        ("LEAD",             "input",  "tests/**/*",                "tests/**/*",                       "Test files", 1),
        ("LEAD",             "input",  "sprint/{:03d}/test-report.md", "sprint/{:03d}/test-report.md", "Test results report", 1),
        ("LEAD",             "output", "src/**/*",                  "src/**/*",                         "Source code files", 1),
        ("LEAD",             "output", "install.sh",                "install.sh",                       "Installation script", 0),
        ("LEAD",             "output", "run.sh",                    "run.sh",                           "Run script", 0),
        ("REVIEW",           "input",  "sprint/{:03d}/spec.md",     "sprint/{:03d}/spec.md",           "Technical specification", 0),
        ("REVIEW",           "input",  "src/**/*",                  "src/**/*",                         "Source code files", 1),
        ("REVIEW",           "input",  "sprint/{:03d}/test-report.md", "sprint/{:03d}/test-report.md", "Test results report from TEST state", 1),
        ("REVIEW",           "output", "sprint/{:03d}/review.md",   "sprint/{:03d}/review.md",         "Sprint review report", 0),
        ("SPRINT_GATE",      "input",  "sprint/{:03d}/review.md",   "sprint/{:03d}/review.md",         "Sprint review report", 1),
        ("SPRINT_GATE",      "input",  "backlog/",                  "backlog/",                         "Backlog directory", 0),
        ("SPRINT_GATE",      "output", "sprint/{:03d}/gate-code.md","sprint/{:03d}/gate-code.md",       "Gate decision file", 0),
    ]

    for state_name, direction, pattern, template, desc, optional in contracts:
        cursor.execute(
            """INSERT OR REPLACE INTO file_contracts
               (state_name, direction, pattern, template, description, optional)
               VALUES (?, ?, ?, ?, ?, ?)""",
            (state_name, direction, pattern, template, desc, optional),
        )

    conn.commit()

    state_count = len(states)
    transition_count = len(transitions)
    contract_count = len(contracts)

    print(f"  Pipeline: {state_count} states, "
          f"{transition_count} transitions, "
          f"{contract_count} contracts seeded.")
