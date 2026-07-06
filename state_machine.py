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


def has_backlog(backlog_file):
    """Return True if the backlog file exists and is non-empty."""
    if not os.path.exists(backlog_file):
        return False
    with open(backlog_file) as f:
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


# ─── main loop ───────────────────────────────────────────────────────────────

def main():
    config_path = sys.argv[1] if len(sys.argv) > 1 and sys.argv[1].startswith("--config=") else None
    if config_path:
        config_path = config_path.split("=", 1)[1]
    cfg = load_config(config_path)

    max_iterations = cfg.get("max_iterations", DEFAULT_CONFIG["max_iterations"])
    max_retries = cfg.get("max_retries", DEFAULT_CONFIG["max_retries"])
    phases = load_phases(cfg)
    scripts = cfg.get("phase_scripts", DEFAULT_CONFIG["phase_scripts"])
    backlog_file = cfg.get("backlog_file", DEFAULT_CONFIG["backlog_file"])
    signal_file = cfg.get("signal_file", DEFAULT_CONFIG["signal_file"])
    ship_command = cfg.get("ship_command", DEFAULT_CONFIG["ship_command"])

    print(f"🚢 Matsya State Machine — max_iterations={max_iterations}, max_retries={max_retries}")
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
                # Gate phase: check backlog
                if has_backlog(backlog_file):
                    print(f"  → Backlog non-empty. Continuing to iteration {iteration + 1}.")
                    # break out of phases, go to next iteration
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
                    success = run_script(script, phase, iteration)
                    if success:
                        break
                    if attempt < max_retries:
                        print(f"     Retrying...")
                    else:
                        print(f"  ✗ Phase {phase} failed after {max_retries} attempts.")

                if not success:
                    print(f"\n  ✗ Iteration {iteration} failed at phase {phase}.")
                    sys.exit(1)

        # else: for-loop completed without break (skip — GATE always breaks or returns)

        iteration += 1

    print(f"\n{'='*60}")
    print(f"  All {max_iterations} iterations completed.")


if __name__ == "__main__":
    main()
