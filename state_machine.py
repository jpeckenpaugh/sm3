#!/usr/bin/env python3
"""
Matsya: Config-driven state machine loop.

Phases: PLAN, WRITE, REVIEW, COMMIT, GATE

For each iteration:
  for each phase:
    retry up to max_retries
  GATE: check backlog → continue or SHIP

Usage:
  python3 state_machine.py [--config config.json]
"""

import json
import os
import sqlite3
import subprocess
import sys
import time
from pathlib import Path


# ─── defaults ────────────────────────────────────────────────────────────────

DEFAULT_CONFIG = {
    "phases": ["PLAN", "WRITE", "REVIEW", "COMMIT", "GATE"],
    "max_iterations": 10,
    "max_retries": 4,
    "backlog_file": "backlog.txt",
    "phase_scripts": {
        "PLAN":   "scripts/phase_plan.sh",
        "WRITE":  "scripts/phase_write.sh",
        "REVIEW": "scripts/phase_review.sh",
        "COMMIT": "git_commit.sh",
        "GATE":   "scripts/phase_gate.sh",
    },
    "signal_file": "vasuki.signal",
    "ship_command": "echo SHIPPING",
}


# ─── helpers ─────────────────────────────────────────────────────────────────

def load_config(path=None):
    """Load config from a JSON file, merging with defaults."""
    cfg = dict(DEFAULT_CONFIG)
    if path and os.path.exists(path):
        with open(path) as f:
            user = json.load(f)
        cfg.update(user)
    # Allow env var override for backlog/signal paths
    if os.environ.get("MATSYA_BACKLOG"):
        cfg["backlog_file"] = os.environ["MATSYA_BACKLOG"]
    if os.environ.get("MATSYA_SIGNAL"):
        cfg["signal_file"] = os.environ["MATSYA_SIGNAL"]
    return cfg


def run_script(script_path, phase_name, iteration):
    """Run a phase script. Return True if exit code 0."""
    if not os.path.exists(script_path):
        print(f"  ⚠  Script not found: {script_path} — skipping")
        return True  # skip missing scripts

    print(f"  ── Running {script_path} ...")
    result = subprocess.run(
        ["bash", script_path, phase_name, str(iteration)],
        capture_output=True,
        text=True,
    )
    if result.stdout:
        for line in result.stdout.strip().split("\n"):
            print(f"     {line}")
    if result.stderr:
        for line in result.stderr.strip().split("\n"):
            print(f"     ! {line}")

    ok = result.returncode == 0
    print(f"  ── {script_path} → {'OK' if ok else 'FAIL'}")
    return ok


def _has_pipeline_tables(db_path):
    """Return True if the database has pipeline_states and pipeline_transitions tables."""
    if not db_path or not os.path.exists(db_path):
        return False
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        cursor.execute(
            "SELECT name FROM sqlite_master WHERE type='table' AND name='pipeline_states'"
        )
        result = cursor.fetchone() is not None
        conn.close()
        return result
    except Exception:
        return False


def has_backlog(backlog_path):
    """Return True if the backlog exists and has items.

    Handles both directories (counts .md files) and plain text files.
    """
    if not os.path.exists(backlog_path):
        return False
    if os.path.isdir(backlog_path):
        # Count files in the directory
        for entry in os.scandir(backlog_path):
            return True  # at least one entry exists
        return False
    # Plain text file
    with open(backlog_path) as f:
        return bool(f.read().strip())


def wait_for_signal(signal_file, poll_secs=5, timeout_secs=300):
    """Poll for Vasuki's signal file. Return True if found."""
    print(f"  ⏳ Waiting for signal file: {signal_file}")
    elapsed = 0
    while elapsed < timeout_secs:
        if os.path.exists(signal_file):
            print(f"  ✅ Signal detected: {signal_file}")
            return True
        time.sleep(poll_secs)
        elapsed += poll_secs
    print(f"  ⏰ Timeout waiting for signal: {signal_file}")
    return False


def load_phases(cfg):
    """Determine the ordered list of phases from config."""
    return cfg.get("phases", DEFAULT_CONFIG["phases"])


# ─── phase logging ────────────────────────────────────────────────────────────

def log_phase_start(conn, sprint_id, phase, iteration, attempt):
    """Insert a phase_runs row with status='running'. Returns the row id."""
    cursor = conn.cursor()
    cursor.execute(
        """INSERT INTO phase_runs (sprint_id, phase, iteration, attempt, status)
           VALUES (?, ?, ?, ?, 'running')""",
        (sprint_id, phase, iteration, attempt),
    )
    conn.commit()
    return cursor.lastrowid


def log_phase_end(conn, run_id, success, output_summary="", error=""):
    """Update a phase_runs row with completion status."""
    cursor = conn.cursor()
    if success:
        cursor.execute(
            """UPDATE phase_runs
               SET status = 'passed',
                   completed_at = strftime('%Y-%m-%dT%H:%M:%SZ', 'now'),
                   output_summary = ?
               WHERE id = ?""",
            (output_summary, run_id),
        )
    else:
        cursor.execute(
            """UPDATE phase_runs
               SET status = 'failed',
                   completed_at = strftime('%Y-%m-%dT%H:%M:%SZ', 'now'),
                   error = ?
               WHERE id = ?""",
            (error, run_id),
        )
    conn.commit()


def complete_sprint(conn, sprint_id, status="completed"):
    """Mark a sprint as completed or failed."""
    cursor = conn.cursor()
    cursor.execute(
        """UPDATE sprints
           SET status = ?,
               completed_at = strftime('%Y-%m-%dT%H:%M:%SZ', 'now')
           WHERE id = ?""",
        (status, sprint_id),
    )
    conn.commit()


# ─── main loop ───────────────────────────────────────────────────────────────

def run_with_config(cfg):
    """Run the state machine with a given config dict.

    This is the programmatic entry point, used by sm.py and other callers.

    If the database has pipeline_states and pipeline_transitions tables,
    this function delegates to the DB-driven pipeline engine (Sprint 03).
    Otherwise it falls back to the hardcoded 5-phase loop (original behaviour).

    The config dict should have the same shape as the default config or
    a loaded config.json.

    Recognised logging keys:
        db_path     — path to SQLite database for phase_runs logging
        sprint_id   — sprint id to log phase runs against
    """
    # Sprint 03: delegate to DB-driven pipeline engine if tables exist
    db_path = cfg.get("db_path")
    if db_path and _has_pipeline_tables(db_path):
        try:
            from pipeline.engine import run_pipeline
            return run_pipeline(cfg)
        except ImportError:
            print("  ⚠  pipeline.engine not available — falling back to hardcoded loop")
        except Exception as e:
            print(f"  ⚠  Pipeline engine error: {e}")
            print("     Falling back to hardcoded loop.")

    max_iterations = cfg.get("max_iterations", DEFAULT_CONFIG["max_iterations"])
    max_retries = cfg.get("max_retries", DEFAULT_CONFIG["max_retries"])
    phases = cfg.get("phases", DEFAULT_CONFIG["phases"])
    scripts = cfg.get("phase_scripts", DEFAULT_CONFIG["phase_scripts"])
    backlog_file = cfg.get("backlog_file", DEFAULT_CONFIG["backlog_file"])
    signal_file = cfg.get("signal_file", DEFAULT_CONFIG["signal_file"])
    ship_command = cfg.get("ship_command", DEFAULT_CONFIG["ship_command"])
    db_path = cfg.get("db_path")
    sprint_id = cfg.get("sprint_id")

    # Open DB connection for phase logging (optional)
    log_conn = None
    if db_path and sprint_id:
        log_conn = sqlite3.connect(db_path)

    try:
        print(f"🚢 Matsya State Machine — max_iterations={max_iterations}, max_retries={max_retries}")
        if sprint_id:
            print(f"   Sprint #{sprint_id} — logging to {db_path}")
        print(f"   Phases: {', '.join(phases)}")
        print()

        iteration = 1
        while iteration <= max_iterations:
            print(f"{'='*60}")
            print(f"  Iteration {iteration}")
            print(f"{'='*60}")

            for phase in phases:
                print(f"\n  ▶ Phase: {phase}")

                if phase == "GATE":
                    if has_backlog(backlog_file):
                        print(f"  → Backlog non-empty. Continuing to iteration {iteration + 1}.")
                        break
                    else:
                        print(f"  → Backlog empty. Shipping.")
                        subprocess.run(["bash", "-c", ship_command])
                        print(f"  → Waiting for Vasuki signal...")
                        if wait_for_signal(signal_file):
                            print(f"  → Signal received. Continuing to next iteration.")
                            break
                        else:
                            print(f"  → No signal. Exiting.")
                            return
                else:
                    script = scripts.get(phase)
                    if not script:
                        print(f"  ⚠  No script configured for phase {phase} — skipping")
                        continue

                    success = False
                    for attempt in range(1, max_retries + 1):
                        print(f"     Attempt {attempt}/{max_retries}")

                        # Log phase start
                        run_id = None
                        if log_conn and sprint_id:
                            run_id = log_phase_start(log_conn, sprint_id, phase, iteration, attempt)

                        success = run_script(script, phase, iteration)

                        # Log phase end
                        if log_conn and run_id:
                            output = f"Phase {phase} iter {iteration} attempt {attempt}"
                            if success:
                                log_phase_end(log_conn, run_id, True, output_summary=output)
                            else:
                                log_phase_end(log_conn, run_id, False, error=f"Script failed: {script}")

                        if success:
                            break
                        if attempt < max_retries:
                            print(f"     Retrying...")
                        else:
                            print(f"  ✗ Phase {phase} failed after {max_retries} attempts.")

                    if not success:
                        print(f"\n  ✗ Iteration {iteration} failed at phase {phase}.")
                        # Log sprint failure
                        if log_conn and sprint_id:
                            complete_sprint(log_conn, sprint_id, status="failed")
                        sys.exit(1)

            iteration += 1

        # All iterations completed successfully
        print(f"\n{'='*60}")
        print(f"  All {max_iterations} iterations completed.")
        if log_conn and sprint_id:
            complete_sprint(log_conn, sprint_id, status="completed")

    except KeyboardInterrupt:
        print("\n  ⌨️ User canceled with Ctrl-C")
        if log_conn and sprint_id:
            try:
                complete_sprint(log_conn, sprint_id, status="aborted")
            except Exception:
                pass
        sys.exit(130)
    finally:
        if log_conn:
            log_conn.close()


def main():
    config_path = sys.argv[1] if len(sys.argv) > 1 and sys.argv[1].startswith("--config=") else None
    if config_path:
        config_path = config_path.split("=", 1)[1]
    cfg = load_config(config_path)

    run_with_config(cfg)


if __name__ == "__main__":
    main()
