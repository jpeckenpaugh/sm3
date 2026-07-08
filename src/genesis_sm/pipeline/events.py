"""
genesis_sm.pipeline.events — Phase event logging.

Provides:
  log_phase_event()    — insert a high-resolution event row
  read_phase_events()  — query events for a sprint (used by sm log --events)

The table (phase_events) exists in schema.sql. This module is the
first module built in Sprint 03 because it is the simplest — it proves
the DB connection and gives visible output from day one.

Migrated from the project root (pipeline/events.py) into the genesis-sm
package in Sprint 05.
"""

import sqlite3
from typing import Optional


def log_phase_event(
    db: sqlite3.Connection,
    sprint_id: int,
    phase: str,
    iteration: int,
    attempt: int,
    event_type: str,
    event_data: str = "",
) -> None:
    """Insert a single phase event row.

    Call this at each significant point during a phase's lifecycle:
    phase_start, phase_script_start, phase_script_exit, contract_check,
    contract_missing, escalation_written, retry, phase_end, etc.
    """
    db.execute(
        """INSERT INTO phase_events
           (sprint_id, phase, iteration, attempt, event_type, event_data)
           VALUES (?, ?, ?, ?, ?, ?)""",
        (sprint_id, phase, iteration, attempt, event_type, event_data),
    )
    db.commit()


def read_phase_events(
    db: sqlite3.Connection,
    sprint_id: int,
    as_json: bool = False,
) -> list:
    """Return all events for a given sprint, ordered by created_at.

    If as_json=True, returns a list of dicts for JSON serialization.
    Otherwise returns raw sqlite3.Row objects.
    """
    db.row_factory = sqlite3.Row if not as_json else sqlite3.Row
    cursor = db.execute(
        """SELECT id, sprint_id, phase, iteration, attempt,
                  event_type, event_data, created_at
           FROM phase_events
           WHERE sprint_id = ?
           ORDER BY created_at ASC""",
        (sprint_id,),
    )
    rows = cursor.fetchall()

    if as_json:
        return [
            {
                "id": r["id"],
                "sprint_id": r["sprint_id"],
                "phase": r["phase"],
                "iteration": r["iteration"],
                "attempt": r["attempt"],
                "event_type": r["event_type"],
                "event_data": r["event_data"],
                "created_at": r["created_at"],
            }
            for r in rows
        ]
    return rows


def display_events_table(events: list) -> None:
    """Print events in a human-readable timeline table."""
    if not events:
        print("  No events recorded for this sprint.")
        return

    headers = ("Timestamp", "Phase", "Iter", "Att", "Event", "Data")
    col_widths = (28, 12, 6, 4, 22, 60)
    fmt = "  ".join("{{:<{}}}".format(w) for w in col_widths)
    print(fmt.format(*headers))
    print("  ".join("─" * w for w in col_widths))

    for ev in events:
        ts = ev["created_at"] if isinstance(ev, dict) else ev[7]
        phase = ev["phase"] if isinstance(ev, dict) else ev[2]
        it = ev["iteration"] if isinstance(ev, dict) else ev[3]
        att = ev["attempt"] if isinstance(ev, dict) else ev[4]
        etype = ev["event_type"] if isinstance(ev, dict) else ev[5]
        edata = ev["event_data"] if isinstance(ev, dict) else ev[6]

        # Truncate event_data for display
        edata_str = (edata[:57] + "...") if len(edata) > 60 else edata
        print(fmt.format(ts, phase, it, att, etype, edata_str))
