"""
genesis_sm.pipeline.engine — DB-driven state machine loop.

Reads pipeline_states and pipeline_transitions from the database
to determine the phase sequence, rather than using a hardcoded list.

This is the spine of Sprint 03. All other features (contracts, escalation,
events) hook into this loop.

Usage (called from genesis_sm.state_machine's run_with_config):
    from genesis_sm.pipeline.engine import run_pipeline
    run_pipeline(cfg)

Migrated from the project root (pipeline/engine.py) into the genesis-sm
package in Sprint 05.
"""

import json
import os
import sqlite3
import subprocess
import sys
import time
from pathlib import Path
from typing import Any, Optional

# Reuse utilities from the existing state machine
from genesis_sm.state_machine import run_script, has_backlog, wait_for_signal
from genesis_sm.state_machine import log_phase_start, log_phase_end, complete_sprint

from genesis_sm.pipeline.events import log_phase_event
from genesis_sm.pipeline.dispatch import handshake_sync, dispatch_sync, build_request, record_dispatch


# ─── DB loaders ───────────────────────────────────────────────────────────────

def _load_states(conn: sqlite3.Connection) -> list[dict]:
    """Return all pipeline states ordered by id."""
    cursor = conn.execute(
        "SELECT id, name, description, agent_name FROM pipeline_states ORDER BY id"
    )
    return [
        {
            "id": r[0],
            "name": r[1],
            "description": r[2],
            "agent_name": r[3] or "",
        }
        for r in cursor.fetchall()
    ]


def _load_transitions(conn: sqlite3.Connection) -> list[dict]:
    """Return all pipeline transitions ordered by from_state_id, priority."""
    cursor = conn.execute(
        """SELECT id, from_state_id, to_state_id, guard_expression,
                  is_parallel, priority, description
           FROM pipeline_transitions
           ORDER BY from_state_id, priority"""
    )
    return [
        {
            "id": r[0],
            "from_state_id": r[1],
            "to_state_id": r[2],
            "guard_expression": r[3] or "",
            "is_parallel": bool(r[4]),
            "priority": r[5],
            "description": r[6],
        }
        for r in cursor.fetchall()
    ]


# ─── Guard evaluation ────────────────────────────────────────────────────────

def _evaluate_guard(guard: str, ctx: dict) -> bool:
    """Evaluate a simple named guard condition against runtime context.

    Supported guards:
        "" or "true"         → always True
        "backlog_exists"      → ctx["backlog_file"] has items
        "backlog_empty"       → ctx["backlog_file"] has no items
        "max_iterations_reached" → ctx["iteration"] > ctx["max_iterations"]
        "tests_passed"        → ctx.get("tests_passed", False)
        anything else         → False (unknown guard = don't match)
    """
    if not guard or guard == "true":
        return True
    if guard == "backlog_exists":
        return has_backlog(ctx.get("backlog_file", "backlog"))
    if guard == "backlog_empty":
        return not has_backlog(ctx.get("backlog_file", "backlog"))
    if guard == "max_iterations_reached":
        return ctx.get("iteration", 1) > ctx.get("max_iterations", 10)
    if guard == "tests_passed":
        return ctx.get("tests_passed", False)
    # Unknown guard — do not match
    return False


# ─── Script resolution ──────────────────────────────────────────────────────

def _resolve_script(state_name: str, cfg: dict) -> Optional[str]:
    """Resolve the phase script path for a given state.

    Checks, in order:
    1. cfg["phase_scripts"][state_name] (from config.json or CLI)
    2. A default script path: scripts/phase_<lower>.sh
    3. None (skip)
    """
    scripts = cfg.get("phase_scripts", {})
    if state_name in scripts:
        return scripts[state_name]
    default_path = f"scripts/phase_{state_name.lower()}.sh"
    if os.path.exists(default_path):
        return default_path
    return None


# ─── Transition resolution ──────────────────────────────────────────────────

def _advance(
    state_name: str,
    transitions: list[dict],
    name_to_id: dict,
    id_to_name: dict,
    ctx: dict,
) -> Optional[str]:
    """Evaluate outgoing transitions from state_name and return the next state name.

    Returns:
        Next state name (str) if a matching transition is found
        None if a terminal transition (to_state_id is None) matches
        state_name if no transition matches (should not happen in a well-formed pipeline)
    """
    from_id = name_to_id.get(state_name)
    if from_id is None:
        return None

    candidates = [t for t in transitions if t["from_state_id"] == from_id]

    if not candidates:
        # No outgoing transitions — terminal
        return None

    for t in candidates:
        if _evaluate_guard(t["guard_expression"], ctx):
            if t["to_state_id"] is None:
                return None  # terminal transition
            next_name = id_to_name.get(t["to_state_id"])
            return next_name if next_name else state_name

    # No guard matched — stay in current state
    return state_name


# ─── Contract verification (ft012) ──────────────────────────────────────────

def _verify_contracts(
    conn: sqlite3.Connection,
    state_name: str,
    sprint_id: int,
    iteration: int,
    attempt: int,
) -> list[dict]:
    """Verify file contracts for the current state.

    Reads file_contracts rows matching state_name, globs the patterns,
    logs matches and misses as phase_events. Returns a list of
    verification results.

    Called after the phase script completes. Does not fail the phase
    on missing optional contracts.
    """
    cursor = conn.execute(
        """SELECT direction, pattern, description, optional
           FROM file_contracts
           WHERE state_name = ?
           ORDER BY direction, id""",
        (state_name,),
    )
    contracts = cursor.fetchall()

    results = []
    for direction, pattern, description, optional in contracts:
        matched = list(Path(".").glob(pattern))
        is_missing = len(matched) == 0

        if direction == "output" and is_missing and not optional:
            event_type = "contract_missing"
            event_data = f"output pattern '{pattern}' ({description})"
            log_phase_event(conn, sprint_id, state_name, iteration, attempt,
                            event_type, event_data)
            results.append({"pattern": pattern, "status": "missing", "optional": False})
        else:
            event_type = "contract_check"
            event_data = f"{direction} {pattern}: {len(matched)} file(s)"
            log_phase_event(conn, sprint_id, state_name, iteration, attempt,
                            event_type, event_data)
            results.append({"pattern": pattern, "status": "ok", "count": len(matched)})

    return results


def _write_contract_manifest(
    state_name: str,
    sprint_number: int,
    results: list[dict],
) -> None:
    """Write a JSON manifest of contract verification results.

    Path: sprint/<N>/.contracts/<state>.json
    """
    manifest_dir = Path(f"sprint/{sprint_number}/.contracts")
    manifest_dir.mkdir(parents=True, exist_ok=True)
    manifest_path = manifest_dir / f"{state_name.lower()}.json"

    manifest = {
        "state": state_name,
        "sprint": sprint_number,
        "contracts": results,
    }
    with open(manifest_path, "w") as f:
        json.dump(manifest, f, indent=2)


# ─── Escalation detection (ft013) ───────────────────────────────────────────

def _check_escalations(state_name: str) -> Optional[dict]:
    """Check for escalation files in .escalation/<state>/.

    Returns the first escalation file's content if found, None otherwise.
    """
    escalation_dir = Path(f".escalation/{state_name}")
    if not escalation_dir.exists():
        return None

    files = sorted(escalation_dir.glob("*.md"))
    if not files:
        return None

    content = files[0].read_text().strip()
    return {"file": str(files[0].relative_to(".")), "content": content}


# ─── Agent dispatch helpers ──────────────────────────────────────────────────

def _resolve_agent_name(state: dict, cfg: dict) -> str:
    """Determine the agent name to dispatch to for this state.

    Priority:
    1. pipeline_states.agent_name (full derived name from DB, e.g. 'scribe-PLAN')
    2. profile_name + "-" + state_name (derived from the run's --profile)
    3. empty string (no agent dispatch)
    """
    db_agent = state.get("agent_name", "") or ""
    if db_agent.strip():
        return db_agent.strip()

    state_name = state.get("name", "")
    profile_cfg = cfg.get("profile", {})
    profile_name = profile_cfg.get("name", "")
    if profile_name:
        return f"{profile_name}-{state_name}"

    return ""


def _load_contracts(conn: sqlite3.Connection, state_name: str) -> list[dict]:
    """Load file_contracts for a given state."""
    cursor = conn.execute(
        """SELECT direction, pattern, template, description, optional
           FROM file_contracts
           WHERE state_name = ?
           ORDER BY direction, id""",
        (state_name,),
    )
    return [
        {
            "direction": r[0],
            "pattern": r[1],
            "template": r[2] or "",
            "description": r[3],
            "optional": bool(r[4]),
        }
        for r in cursor.fetchall()
    ]


def _post_phase(
    conn: sqlite3.Connection,
    sprint_id: int,
    state_name: str,
    iteration: int,
    attempt: int,
    sprint_number: int,
    cfg: dict,
) -> None:
    """Run post-phase hooks: contract verification and escalation check."""
    # Contract verification (ft012)
    if state_name != "GATE":
        try:
            contract_results = _verify_contracts(
                conn, state_name, sprint_id, iteration, attempt
            )
            if sprint_number:
                _write_contract_manifest(
                    state_name, sprint_number, contract_results
                )
        except Exception as e:
            print(f"  ⚠  Contract verification error: {e}")

    # Escalation check (ft013)
    escalation = _check_escalations(state_name)
    if escalation:
        print(f"  ⚑ Escalation: {escalation['file']}")
        print(f"    {escalation['content'][:200]}")
        log_phase_event(
            conn, sprint_id, state_name, iteration, attempt,
            "escalation_written",
            f"{escalation['file']}: {escalation['content'][:100]}",
        )
        print(f"  → Sprint blocked. Resolve escalation and re-run with --resume.")
        if sprint_id:
            complete_sprint(conn, sprint_id, status="blocked")
        sys.exit(1)


def _finish_pipeline(conn: sqlite3.Connection, sprint_id: int) -> None:
    """Mark the sprint as completed when the pipeline reaches a terminal state."""
    print(f"\n  Pipeline complete (terminal state reached).")
    if sprint_id:
        complete_sprint(conn, sprint_id, status="completed")


def _run_script_retry(
    conn: sqlite3.Connection,
    sprint_id: int,
    state_name: str,
    iteration: int,
    script: str,
    max_retries: int,
    cfg: dict,
) -> None:
    """Run a phase script with retries, including phase_runs logging (Sprint 02)."""
    for attempt in range(1, max_retries + 1):
        print(f"     Attempt {attempt}/{max_retries}")
        log_phase_event(conn, sprint_id, state_name, iteration, attempt,
                        "phase_script_start", script)

        run_id = None
        if sprint_id:
            run_id = log_phase_start(
                conn, sprint_id, state_name, iteration, attempt,
            )

        success = run_script(script, state_name, iteration)

        log_phase_event(conn, sprint_id, state_name, iteration, attempt,
                        "phase_script_exit",
                        f"exit_code={0 if success else 1}")

        if sprint_id and run_id:
            output = f"Phase {state_name} iter {iteration} attempt {attempt}"
            if success:
                log_phase_end(conn, run_id, True, output_summary=output)
            else:
                log_phase_end(conn, run_id, False, error=f"Script failed: {script}")

        if success:
            return
        if attempt < max_retries:
            print(f"     Retrying...")
            log_phase_event(conn, sprint_id, state_name, iteration, attempt,
                            "retry", f"attempt {attempt} failed, retrying")
        else:
            print(f"  ✗ Phase {state_name} failed after {max_retries} attempts.")

    print(f"\n  ✗ Iteration {iteration} failed at phase {state_name}.")
    if sprint_id:
        complete_sprint(conn, sprint_id, status="failed")
    sys.exit(1)


# ─── The pipeline loop ──────────────────────────────────────────────────────

def run_pipeline(cfg: dict) -> None:
    """Run the DB-driven pipeline loop.

    cfg keys accepted (all optional unless noted):
        db_path        — path to SQLite database (required for pipeline mode)
        sprint_id      — sprint id for logging (required)
        sprint_number  — sprint number (for contract manifest paths)
        profile        — profile dict (name, version, header, permissions, assembled_body)
        max_iterations — max iterations (default: 10)
        max_retries    — max retries per phase (default: 4)
        phase_scripts  — dict of state_name → script path overrides
        backlog_file   — path to backlog file/dir (default: "backlog")
        signal_file    — path to Vasuki signal file (default: "vasuki.signal")
        ship_command   — shell command to run on ship (default: "echo SHIPPING")
        resume         — if True, check for unresolved escalations before starting
    """
    db_path = cfg.get("db_path")
    sprint_id = cfg.get("sprint_id")

    if not db_path or not sprint_id:
        print("  ✗ Pipeline engine requires db_path and sprint_id in config.")
        sys.exit(1)

    # ── Config defaults ──────────────────────────────────────────────────
    max_iterations = cfg.get("max_iterations", 10)
    max_retries = cfg.get("max_retries", 4)
    backlog_file = cfg.get("backlog_file", "backlog")
    signal_file = cfg.get("signal_file", "vasuki.signal")
    ship_command = cfg.get("ship_command", "echo SHIPPING")
    sprint_number = cfg.get("sprint_number", sprint_id)
    resume_mode = cfg.get("resume", False)
    target_feature_count = cfg.get("target_feature_count", "ALL")

    conn = sqlite3.connect(db_path)
    try:
        # ── Load pipeline topology ──────────────────────────────────────
        states = _load_states(conn)
        transitions = _load_transitions(conn)

        if not states:
            print("  ✗ No pipeline states found in database. Run 'sm seed' first.")
            sys.exit(1)

        state_map = {s["name"]: s for s in states}
        name_to_id = {s["name"]: s["id"] for s in states}
        id_to_name = {s["id"]: s["name"] for s in states}
        start_state = states[0]["name"]

        print(f"🚢 Pipeline Engine — {len(states)} states, {len(transitions)} transitions")
        print(f"   Sprint #{sprint_number} — logging to {db_path}")
        print(f"   Max iterations: {max_iterations}, max retries: {max_retries}")
        print()

        # Build runtime context for guard evaluation
        ctx = {
            "backlog_file": backlog_file,
            "signal_file": signal_file,
            "max_iterations": max_iterations,
            "max_retries": max_retries,
            "tests_passed": True,
        }

        # ── Resume mode: check for unresolved escalations ──────────────
        if resume_mode:
            for state_name in state_map:
                escalation = _check_escalations(state_name)
                if escalation:
                    print(f"  ⚑ Unresolved escalation: {escalation['file']}")
                    print(f"    {escalation['content'][:200]}")
                    print(f"  → Resolve the escalation and re-run.")
                    return

        current_state = start_state
        iteration = 1

        # ── Main loop ──────────────────────────────────────────────────
        while iteration <= max_iterations:
            print(f"{'='*60}")
            print(f"  Iteration {iteration}")
            print(f"{'='*60}")

            ctx["iteration"] = iteration

            # Walk through states via transitions
            while current_state:
                state = state_map.get(current_state)
                if not state:
                    print(f"  ✗ Unknown state: {current_state}")
                    sys.exit(1)

                state_name = state["name"]
                print(f"\n  ▶ Phase: {state_name}")

                # Log phase start event
                log_phase_event(conn, sprint_id, state_name, iteration, 1,
                                "phase_start", f"Entering {state_name}")

                # ── Agent dispatch or script resolution ─────────────────
                agent_name = _resolve_agent_name(state, cfg)

                if agent_name and state_name != "COMMIT":
                    # Agent dispatch path
                    print(f"  → Agent: {agent_name}")
                    log_phase_event(conn, sprint_id, state_name, iteration, 1,
                                    "agent_handshake_start", agent_name)

                    try:
                        # Step 1: Handshake
                        handshake_result = handshake_sync(
                            agent_name=agent_name,
                            project_dir=os.getcwd(),
                            timeout=cfg.get("agent_timeout", 120),
                        )
                        log_phase_event(conn, sprint_id, state_name, iteration, 1,
                                        "agent_handshake_done",
                                        f"session={handshake_result.session_id}")
                        print(f"    Session: {handshake_result.session_id}")
                        if handshake_result.confirmed_modes:
                            print(f"    Modes: {', '.join(handshake_result.confirmed_modes)}")

                        # Step 2: Build request text from contracts
                        contracts = _load_contracts(conn, state_name)
                        request_text = build_request(
                            state_name, sprint_number, contracts,
                        )
                        # Append target_feature_count for SPRINT_PLANNING
                        if state_name == "SPRINT_PLANNING":
                            request_text += f" COUNT:{target_feature_count}"
                        print(f"    Request: {request_text}")

                        # Step 3: Dispatch work
                        log_phase_event(conn, sprint_id, state_name, iteration, 1,
                                        "agent_dispatch_start", request_text[:200])
                        dispatch_result = dispatch_sync(
                            agent_name=agent_name,
                            request_text=request_text,
                            project_dir=os.getcwd(),
                            timeout=cfg.get("agent_timeout", 600),
                        )
                        log_phase_event(conn, sprint_id, state_name, iteration, 1,
                                        "agent_response",
                                        dispatch_result.response_text[:200])

                        # Record dispatch
                        record_dispatch(
                            conn, sprint_id,
                            handshake_result.session_id,
                            agent_name, request_text,
                            dispatch_result.response_text,
                            status="completed",
                        )
                        print(f"    Response: {len(dispatch_result.response_text)} chars")

                    except Exception as e:
                        log_phase_event(conn, sprint_id, state_name, iteration, 1,
                                        "agent_error", str(e))
                        print(f"  ✗ Agent dispatch failed: {e}")
                        script = _resolve_script(state_name, cfg)
                        if script:
                            print(f"  → Falling back to script: {script}")
                            _run_script_retry(conn, sprint_id, state_name,
                                              iteration, script, max_retries, cfg)
                            _post_phase(conn, sprint_id, state_name, iteration,
                                        1, sprint_number, cfg)
                            current_state = _advance(state_name, transitions,
                                                     name_to_id, id_to_name, ctx)
                            if current_state is None:
                                _finish_pipeline(conn, sprint_id)
                                return
                            continue
                        else:
                            print(f"  ✗ No fallback script for {state_name}")
                            sys.exit(1)

                    # Post-dispatch hooks
                    _post_phase(conn, sprint_id, state_name, iteration,
                                1, sprint_number, cfg)
                    log_phase_event(conn, sprint_id, state_name, iteration, 1,
                                    "phase_end", "passed (agent dispatch)")
                    current_state = _advance(state_name, transitions,
                                             name_to_id, id_to_name, ctx)
                    if current_state is None:
                        _finish_pipeline(conn, sprint_id)
                        return
                    continue

                # ── Script path (fallback when no agent) ────────────────
                script = _resolve_script(state_name, cfg)

                if script is None:
                    print(f"  ⚠  No script for phase {state_name} — skipping")
                    log_phase_event(conn, sprint_id, state_name, iteration, 1,
                                    "phase_end", "skipped (no script)")
                    current_state = _advance(state_name, transitions,
                                             name_to_id, id_to_name, ctx)
                    continue

                # ── GATE phase special handling ────────────────────────
                if state_name == "GATE":
                    log_phase_event(conn, sprint_id, state_name, iteration, 1,
                                    "phase_script_start", script)
                    success = run_script(script, state_name, iteration)
                    log_phase_event(conn, sprint_id, state_name, iteration, 1,
                                    "phase_script_exit",
                                    f"exit_code={0 if success else 1}")

                    if has_backlog(backlog_file):
                        print(f"  → Backlog non-empty. Continuing.")
                        log_phase_event(conn, sprint_id, state_name, iteration, 1,
                                        "phase_end", "backlog non-empty, continuing")
                        current_state = _advance(state_name, transitions,
                                                 name_to_id, id_to_name, ctx)
                        if current_state == start_state or current_state is None:
                            break
                    else:
                        print(f"  → Backlog empty. Shipping.")
                        subprocess.run(["bash", "-c", ship_command])
                        print(f"  → Waiting for Vasuki signal...")
                        if wait_for_signal(signal_file):
                            print(f"  → Signal received. Continuing.")
                            log_phase_event(conn, sprint_id, state_name, iteration, 1,
                                            "phase_end", "signal received, continuing")
                            current_state = start_state
                            break
                        else:
                            print(f"  → No signal. Exiting.")
                            log_phase_event(conn, sprint_id, state_name, iteration, 1,
                                            "phase_end", "no signal, terminating")
                            if sprint_id:
                                complete_sprint(conn, sprint_id, status="completed")
                            return
                else:
                    # ── Regular phase: retry loop ──────────────────────────
                    _run_script_retry(conn, sprint_id, state_name, iteration,
                                      script, max_retries, cfg)

                # ── Post-phase hooks ──────────────────────────────────────
                _post_phase(conn, sprint_id, state_name, iteration, 1,
                            sprint_number, cfg)

                log_phase_event(conn, sprint_id, state_name, iteration, 1,
                                "phase_end", "passed")

                # ── Advance to next state ─────────────────────────────────
                current_state = _advance(state_name, transitions,
                                         name_to_id, id_to_name, ctx)
                if current_state is None:
                    _finish_pipeline(conn, sprint_id)
                    return

            iteration += 1
            current_state = start_state

        # All iterations completed
        print(f"\n{'='*60}")
        print(f"  All {max_iterations} iterations completed.")
        if sprint_id:
            complete_sprint(conn, sprint_id, status="completed")

    except KeyboardInterrupt:
        print("\n  ⌨️  User canceled with Ctrl-C")
        if sprint_id:
            try:
                complete_sprint(conn, sprint_id, status="aborted")
            except Exception:
                pass
        sys.exit(130)
    finally:
        conn.close()
