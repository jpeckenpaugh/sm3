#!/usr/bin/env python3
"""
Matsya: Command-line interface for the state machine system.

Usage:
    sm seed                    Populate database from seed files
    sm run --profile <name>    Load profile and start state machine loop
    sm list profiles           Display all profiles
    sm list components         Display all components
    sm status                  Show current system state
    sm generate agent <name>   Render a profile as an OpenCode agent file

Python standard library only — no external dependencies.
"""

import argparse
import datetime
import json
import os
import sqlite3
import sys
from pathlib import Path


# ─── Constants ──────────────────────────────────────────────────────────────

DEFAULT_DB = "matsya.db"
SM_CONFIG_FILE = ".sm-config.json"
REGISTRY_DIR = os.path.expanduser("~/.sm")
REGISTRY_FILE = os.environ.get("SM_PROJECTS_PATH") or os.path.join(REGISTRY_DIR, "projects.json")


# ─── Project / DB resolution ────────────────────────────────────────────────

def find_sm_config(start_dir=None):
    """Walk up from start_dir looking for .sm-config.json. Return its path or None."""
    if start_dir is None:
        start_dir = os.getcwd()
    current = os.path.abspath(start_dir)
    while True:
        candidate = os.path.join(current, SM_CONFIG_FILE)
        if os.path.isfile(candidate):
            return candidate
        parent = os.path.dirname(current)
        if parent == current:
            return None
        current = parent


def read_sm_config(config_path):
    """Read a .sm-config.json and return its contents, or None."""
    try:
        with open(config_path) as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        return None


def read_registry():
    """Read ~/.sm/projects.json. Returns dict or {'default': None, 'projects': []}."""
    if not os.path.isfile(REGISTRY_FILE):
        return {"default": None, "projects": []}
    try:
        with open(REGISTRY_FILE) as f:
            return json.load(f)
    except (json.JSONDecodeError, FileNotFoundError):
        return {"default": None, "projects": []}


def write_registry(registry):
    """Write ~/.sm/projects.json, creating directory if needed."""
    os.makedirs(REGISTRY_DIR, exist_ok=True)
    with open(REGISTRY_FILE, "w") as f:
        json.dump(registry, f, indent=2)
        f.write("\n")


def registry_upsert(registry, name, db_path):
    """Add or update a project entry in the registry by name."""
    now = datetime.date.today().isoformat()
    # Check if entry already exists
    for i, proj in enumerate(registry["projects"]):
        if proj["name"] == name:
            registry["projects"][i]["db_path"] = db_path
            registry["projects"][i]["last_opened"] = now
            if "created" not in registry["projects"][i]:
                registry["projects"][i]["created"] = now
            return
    # New entry
    registry["projects"].append({
        "name": name,
        "db_path": db_path,
        "created": now,
        "last_opened": now,
    })


def get_db_path(db_arg=None, allow_missing=False):
    """Resolve database path with full fallback chain.

    Order:
    1. --db <path> flag                         (db_arg)
    2. .sm-config.json in CWD or parent          (auto-discovery)
    3. SM_PROJECT env var → lookup in registry
    4. "default" project in ~/.sm/projects.json
    5. matsya.db in current directory            (compatibility)
    6. → error (or None if allow_missing=True)
    """
    # 1. Explicit --db flag
    if db_arg:
        return db_arg

    # 2. .sm-config.json auto-discovery
    config_path = find_sm_config()
    if config_path:
        config = read_sm_config(config_path)
        if config and config.get("db_path"):
            return config["db_path"]

    # 3. SM_PROJECT env var
    env_project = os.environ.get("SM_PROJECT")
    if env_project:
        registry = read_registry()
        for proj in registry.get("projects", []):
            if proj["name"] == env_project:
                return proj["db_path"]

    # 4. "default" in registry
    registry = read_registry()
    default_name = registry.get("default")
    if default_name:
        for proj in registry.get("projects", []):
            if proj["name"] == default_name:
                return proj["db_path"]

    # 5. Compatibility fallback
    cwd_db = os.path.join(os.getcwd(), DEFAULT_DB)
    if os.path.isfile(cwd_db):
        return cwd_db

    # 6. Error
    if allow_missing:
        return None
    print("✗ No project found. Run 'sm init --db <path>' or specify --db.")
    sys.exit(1)


def get_conn(db_arg=None):
    """Get a SQLite connection using resolved db_path."""
    db_path = get_db_path(db_arg)
    return sqlite3.connect(db_path)


def profile_exists(conn, name):
    """Return True if a profile with the given name exists."""
    cursor = conn.cursor()
    cursor.execute("SELECT 1 FROM profiles WHERE name = ?", (name,))
    return cursor.fetchone() is not None


# ─── Command: seed ──────────────────────────────────────────────────────────

def cmd_seed(args):
    """Run the seed data loader."""
    # Import seed module and delegate
    import seed
    exit_code = seed.seed_database(
        db_path=args.db,
        schema_path=args.schema,
        seed_root=args.seed_root,
    )
    sys.exit(exit_code)


# ─── Command: run ───────────────────────────────────────────────────────────

def cmd_run(args):
    """Load a profile, auto-create a sprint, and start the state machine loop."""
    db_path = get_db_path(args.db)
    conn = sqlite3.connect(db_path)
    try:
        cursor = conn.cursor()

        # 1. Load profile
        cursor.execute(
            "SELECT name, version, header, permissions FROM profiles WHERE name = ?",
            (args.profile,),
        )
        row = cursor.fetchone()
        if row is None:
            print(f"✗ Profile '{args.profile}' not found in database.")
            print("  Run 'sm seed' first, or check the profile name.")
            sys.exit(1)

        profile_name, version, header_json, permissions_json = row
        header = json.loads(header_json)
        permissions = json.loads(permissions_json)

        # 2. Assemble components
        cursor.execute(
            """SELECT c.type, c.name, c.content, pc.order_idx, pc.params
               FROM profile_components pc
               JOIN components c ON pc.component_id = c.id
               JOIN profiles p ON pc.profile_id = p.id
               WHERE p.name = ?
               ORDER BY pc.order_idx""",
            (args.profile,),
        )
        components = cursor.fetchall()

        # 3. Build assembled body text
        body_parts = []
        for comp_type, comp_name, content, order_idx, params_json in components:
            if content:
                body_parts.append(content)
        assembled_body = "\n\n".join(body_parts)

        # 4. Auto-create sprint (driven mode)
        # Ensure sprints table exists
        cursor.execute(
            "SELECT name FROM sqlite_master WHERE type='table' AND name='sprints'"
        )
        if not cursor.fetchone():
            print("✗ Database schema missing 'sprints' table. Run 'sm seed' to update.")
            sys.exit(1)
        cursor.execute("SELECT COALESCE(MAX(number), 0) + 1 FROM sprints")
        next_num = cursor.fetchone()[0]
        now = datetime.datetime.utcnow().strftime('%Y-%m-%dT%H:%M:%SZ')
        cursor.execute(
            """INSERT INTO sprints (number, mode, status, started_at, notes)
               VALUES (?, 'driven', 'active', ?, ?)""",
            (next_num, now, f"Auto-created by sm run --profile {profile_name}"),
        )
        sprint_id = cursor.lastrowid
        conn.commit()
        print(f"  Sprint #{next_num} ({sprint_id}) — driven, active")
        print()

        # 5. Construct config for state machine
        cfg = {}
        config_path = args.config or "config.json"
        if os.path.exists(config_path):
            with open(config_path) as f:
                file_cfg = json.load(f)
            cfg.update(file_cfg)

        # CLI args override config.json
        if args.max_iterations is not None:
            cfg["max_iterations"] = args.max_iterations
        if args.max_retries is not None:
            cfg["max_retries"] = args.max_retries

        # Add profile data
        cfg["profile"] = {
            "name": profile_name,
            "version": version,
            "header": header,
            "permissions": permissions,
            "assembled_body": assembled_body,
        }

        # Add logging config for state machine
        cfg["db_path"] = db_path
        cfg["sprint_id"] = sprint_id

        # Set environment variables for phase scripts to consume
        os.environ["MATSYA_PROFILE"] = profile_name
        os.environ["MATSYA_HEADER"] = header_json
        os.environ["MATSYA_PERMISSIONS"] = permissions_json
        os.environ["MATSYA_BODY"] = assembled_body

        print(f"  Profile: {profile_name} v{version}")
        print(f"  Role:    {header.get('role', 'unknown')}")
        print(f"  Mode:    {header.get('mode', 'all')}")
        print(f"  Temp:    {header.get('temperature', 'N/A')}")
        print(f"  Components: {len(components)} assembled")
        print()

        # 6. Import and run state machine
        from state_machine import run_with_config
        run_with_config(cfg)

    finally:
        conn.close()


# ─── Command: list ──────────────────────────────────────────────────────────

def cmd_list_profiles(args):
    """Display all profiles from the database."""
    conn = get_conn(args.db)
    try:
        cursor = conn.cursor()
        cursor.execute(
            "SELECT name, version, header, permissions FROM profiles ORDER BY name"
        )
        rows = cursor.fetchall()

        if not rows:
            print("No profiles found. Run 'sm seed' first.")
            return

        if args.json:
            # JSON output
            output = []
            for name, version, header_json, permissions_json in rows:
                entry = {
                    "name": name,
                    "version": version,
                    "header": json.loads(header_json),
                    "permissions": json.loads(permissions_json),
                }
                output.append(entry)
            print(json.dumps(output, indent=2))
            return

        # Table output
        if args.verbose:
            # Show more detail
            headers = ("Name", "Version", "Role", "Mode", "Temperature", "Permissions")
            col_widths = [20, 10, 25, 8, 13, 40]
            fmt = "  ".join("{{:<{}}}".format(w) for w in col_widths)
            print(fmt.format(*headers))
            print("  ".join("─" * w for w in col_widths))
            for name, version, header_json, permissions_json in rows:
                header = json.loads(header_json)
                perms = json.loads(permissions_json)
                perms_str = json.dumps(perms, separators=(",", ":"))
                print(fmt.format(
                    name,
                    version,
                    header.get("role", ""),
                    header.get("mode", ""),
                    str(header.get("temperature", "")),
                    perms_str,
                ))
        else:
            # Compact view
            headers = ("Name", "Version", "Role", "Mode", "Temperature")
            col_widths = [20, 10, 25, 8, 13]
            fmt = "  ".join("{{:<{}}}".format(w) for w in col_widths)
            print(fmt.format(*headers))
            print("  ".join("─" * w for w in col_widths))
            for name, version, header_json, permissions_json in rows:
                header = json.loads(header_json)
                print(fmt.format(
                    name,
                    version,
                    header.get("role", ""),
                    header.get("mode", ""),
                    str(header.get("temperature", "")),
                ))
    finally:
        conn.close()


def cmd_list_components(args):
    """Display all components from the database."""
    conn = get_conn(args.db)
    try:
        cursor = conn.cursor()
        cursor.execute(
            "SELECT type, name, content FROM components ORDER BY type, name"
        )
        rows = cursor.fetchall()

        if not rows:
            print("No components found. Run 'sm seed' first.")
            return

        if args.json:
            output = []
            for comp_type, name, content in rows:
                entry = {"type": comp_type, "name": name, "content": content}
                output.append(entry)
            print(json.dumps(output, indent=2))
            return

        # Table output
        truncate_at = args.truncate or 60
        headers = ("Type", "Name", "Content Preview")
        col_widths = [10, 28, truncate_at + 3]
        fmt = "  ".join("{{:<{}}}".format(w) for w in col_widths)
        print(fmt.format(*headers))
        print("  ".join("─" * w for w in col_widths))

        for comp_type, name, content in rows:
            if args.verbose:
                preview = content
            else:
                preview = (content[:truncate_at] + "...") if len(content) > truncate_at else content
            print(fmt.format(comp_type, name, preview))
    finally:
        conn.close()


# ─── Command: status ────────────────────────────────────────────────────────

def cmd_status(args):
    """Show current system state."""
    print("Matsya State Machine — Status")
    print("─" * 35)

    # 1. Check database existence and content
    db_path = get_db_path(args.db, allow_missing=True)
    if os.path.exists(db_path):
        conn = get_conn(args.db)
        try:
            cursor = conn.cursor()
            # Check if profiles table exists
            cursor.execute(
                "SELECT name FROM sqlite_master WHERE type='table' AND name='profiles'"
            )
            if cursor.fetchone():
                cursor.execute("SELECT COUNT(*) FROM profiles")
                profile_count = cursor.fetchone()[0]
                cursor.execute("SELECT COUNT(*) FROM components")
                component_count = cursor.fetchone()[0]
                cursor.execute("SELECT COUNT(*) FROM profile_components")
                pc_count = cursor.fetchone()[0]
                print(f"  Database:     {db_path} (ready)")
                print(f"  Profiles:     {profile_count}")
                print(f"  Components:   {component_count}")
                print(f"  Assemblies:   {pc_count}")
            else:
                print(f"  Database:     {db_path} (no schema — run 'sm seed')")
        finally:
            conn.close()
    else:
        print(f"  Database:     {db_path} (not found — run 'sm seed')")

    # 2. Check backlog
    backlog_path = args.backlog or "backlog"
    if os.path.isdir(backlog_path):
        backlog_files = [f for f in os.listdir(backlog_path) if f.endswith(".md")]
        print(f"  Backlog:      {len(backlog_files)} items")
    elif os.path.isfile(args.backlog or "backlog.txt"):
        # Also check backlog.txt format
        with open(args.backlog or "backlog.txt") as f:
            content = f.read().strip()
        lines = content.split("\n") if content else []
        print(f"  Backlog:      {len(lines)} items (backlog.txt)")
    else:
        print(f"  Backlog:      (not found)")

    # 3. Check signal file
    signal_path = args.signal or "vasuki.signal"
    if os.path.exists(signal_path):
        print(f"  Signal:       present")
    else:
        print(f"  Signal:       absent")

    # 4. Check iteration state file
    state_path = args.state or "matsya_state.json"
    if os.path.exists(state_path):
        with open(state_path) as f:
            state = json.load(f)
        print(f"  Iteration:    {state.get('iteration', '?')} of {state.get('max_iterations', '?')}")
        print(f"  Phase:        {state.get('phase', '?')}")
    else:
        print(f"  State:        Never run — run 'sm run --profile <name>' to begin")

    # 5. Show active profile if set
    active_profile = os.environ.get("MATSYA_PROFILE")
    if active_profile:
        print(f"  Active profile: {active_profile}")


# ─── Command: generate agent ────────────────────────────────────────────────

def cmd_generate_agent(args):
    """Render a profile as an OpenCode agent markdown file."""
    conn = get_conn(args.db)
    try:
        cursor = conn.cursor()

        # 1. Load profile
        cursor.execute(
            "SELECT name, version, header, permissions FROM profiles WHERE name = ?",
            (args.name,),
        )
        row = cursor.fetchone()
        if row is None:
            print(f"✗ Profile '{args.name}' not found in database.")
            print("  Run 'sm seed' first, or check the profile name.")
            sys.exit(1)

        profile_name, version, header_json, permissions_json = row
        header = json.loads(header_json)
        permissions = json.loads(permissions_json)

        # 2. Assemble components in order
        cursor.execute(
            """SELECT c.content
               FROM profile_components pc
               JOIN components c ON pc.component_id = c.id
               JOIN profiles p ON pc.profile_id = p.id
               WHERE p.name = ?
               ORDER BY pc.order_idx""",
            (args.name,),
        )
        component_rows = cursor.fetchall()
        body_parts = [row[0] for row in component_rows if row[0]]
        assembled_body = "\n\n".join(body_parts)

        # 3. Build agent markdown
        description = header.get("role", args.name)
        mode = header.get("mode", "all")
        temperature = header.get("temperature", 0.1)

        # Build permission YAML manually (no PyYAML dependency)
        permission_yaml = _permissions_to_yaml(permissions, indent=0)

        agent_md = f"""---
description: {description}
mode: {mode}
temperature: {temperature}
permission:
{permission_yaml}
---

{assembled_body}
"""

        # 4. Determine output path
        agents_dir = args.output_dir or ".opencode/agents"
        os.makedirs(agents_dir, exist_ok=True)
        output_path = os.path.join(agents_dir, f"{args.name}.md")

        with open(output_path, "w") as f:
            f.write(agent_md)

        print(f"✓ Generated agent file: {output_path}")
        print(f"  Profile: {profile_name} v{version}")
        print(f"  Components: {len(component_rows)} assembled")

    finally:
        conn.close()


# ─── Command: log ────────────────────────────────────────────────────────────

def cmd_log(args):
    """Display execution history from the database."""
    db_path = get_db_path(args.db, allow_missing=True)
    if not db_path or not os.path.isfile(db_path):
        print("No database found. Run 'sm init --db <path>' first.")
        sys.exit(1)

    conn = sqlite3.connect(db_path)
    try:
        # Verify schema
        cursor = conn.cursor()
        cursor.execute(
            "SELECT name FROM sqlite_master WHERE type='table' AND name='sprints'"
        )
        if not cursor.fetchone():
            print("No sprints table found. Run 'sm seed' to update the database schema.")
            sys.exit(1)

        if args.json:
            # JSON output — sprints with optional phase detail
            cursor = conn.cursor()
            if args.sprint is not None:
                cursor.execute(
                    "SELECT id, number, mode, status, started_at, completed_at, notes FROM sprints WHERE number = ? ORDER BY number",
                    (args.sprint,),
                )
            else:
                cursor.execute(
                    "SELECT id, number, mode, status, started_at, completed_at, notes FROM sprints ORDER BY number"
                )
            sprints_rows = cursor.fetchall()

            output = []
            for sid, num, mode, status, started, completed, notes in sprints_rows:
                entry = {
                    "id": sid,
                    "number": num,
                    "mode": mode,
                    "status": status,
                    "started_at": started,
                    "completed_at": completed,
                    "notes": notes,
                }
                if args.show_phases:
                    cursor.execute(
                        """SELECT phase, iteration, attempt, status, started_at, completed_at, output_summary, error
                           FROM phase_runs WHERE sprint_id = ? ORDER BY id""",
                        (sid,),
                    )
                    entry["phases"] = [
                        {
                            "phase": p, "iteration": it, "attempt": at,
                            "status": s, "started_at": st, "completed_at": co,
                            "output_summary": ou, "error": er,
                        }
                        for p, it, at, s, st, co, ou, er in cursor.fetchall()
                    ]
                output.append(entry)

            if not output:
                print("[]")
            else:
                print(json.dumps(output, indent=2))
            return

        # Human-readable output
        cursor = conn.cursor()
        if args.sprint is not None:
            cursor.execute(
                "SELECT id, number, mode, status, started_at, completed_at, notes FROM sprints WHERE number = ? ORDER BY number",
                (args.sprint,),
            )
        else:
            cursor.execute(
                "SELECT id, number, mode, status, started_at, completed_at, notes FROM sprints ORDER BY number"
            )
        sprints_rows = cursor.fetchall()

        if not sprints_rows:
            print("No sprints recorded. Start one with 'sm sprint start --number 1 --mode driven'.")
            return

        for sid, num, mode, status, started, completed, notes in sprints_rows:
            status_line = f"Sprint {num} ({mode}, {status})"
            if started:
                status_line += f" — started {started[:10]}"
            if completed:
                status_line += f" — completed {completed[:10]}"
            print(status_line)
            print("─" * len(status_line))

            if args.show_phases:
                cursor.execute(
                    """SELECT phase, iteration, attempt, status, started_at, completed_at, output_summary, error
                       FROM phase_runs WHERE sprint_id = ? ORDER BY id""",
                    (sid,),
                )
                phase_rows = cursor.fetchall()
                if phase_rows:
                    # Column alignment
                    headers = ("Phase", "Iter", "Att", "Status", "Summary")
                    print(f"  {headers[0]:12s} {headers[1]:6s} {headers[2]:4s} {headers[3]:8s} {headers[4]:40s}")
                    print(f"  {'─'*12} {'─'*6} {'─'*4} {'─'*8} {'─'*40}")
                    for ph, it, at, st, p_started, p_completed, summary, err in phase_rows:
                        trunc_summary = (summary[:37] + "...") if len(summary) > 40 else summary
                        print(f"  {ph:12s} {it:6d} {at:4d} {st:8s} {trunc_summary:40s}")
                else:
                    print("  No phase log (manual sprint)")
            else:
                # Count phases
                cursor.execute(
                    "SELECT COUNT(*) FROM phase_runs WHERE sprint_id = ?",
                    (sid,),
                )
                phase_count = cursor.fetchone()[0]
                if phase_count > 0:
                    print(f"  {phase_count} phase run(s) logged")
                else:
                    print("  No phase log (manual sprint)")

            if notes:
                print(f"  Notes: {notes[:80]}")
            print()

    finally:
        conn.close()


# ─── Command: sprint ─────────────────────────────────────────────────────────

def cmd_sprint(args):
    """Manage sprint lifecycle (start, complete, fail, note)."""
    db_path = get_db_path(args.db)
    conn = sqlite3.connect(db_path)
    try:
        cursor = conn.cursor()
        # Verify schema
        cursor.execute(
            "SELECT name FROM sqlite_master WHERE type='table' AND name='sprints'"
        )
        if not cursor.fetchone():
            print("No sprints table found. Run 'sm seed' to update the database schema.")
            sys.exit(1)

        now = datetime.datetime.utcnow().strftime('%Y-%m-%dT%H:%M:%SZ')

        if args.sprint_action == "start":
            # Check for duplicate
            cursor.execute("SELECT id FROM sprints WHERE number = ?", (args.number,))
            if cursor.fetchone():
                print(f"✗ Sprint {args.number} already exists. Use a different number or complete the existing sprint first.")
                sys.exit(1)
            mode = args.mode or "driven"
            cursor.execute(
                """INSERT INTO sprints (number, mode, status, started_at, notes)
                   VALUES (?, ?, 'active', ?, ?)""",
                (args.number, mode, now, args.notes or ""),
            )
            conn.commit()
            print(f"✓ Sprint {args.number} started (mode: {mode})")

        elif args.sprint_action == "complete":
            cursor.execute(
                "UPDATE sprints SET status = 'completed', completed_at = ? WHERE number = ?",
                (now, args.number),
            )
            if cursor.rowcount == 0:
                print(f"✗ Sprint {args.number} not found.")
                sys.exit(1)
            conn.commit()
            print(f"✓ Sprint {args.number} completed")

        elif args.sprint_action == "fail":
            reason = args.reason or "No reason given"
            cursor.execute(
                "UPDATE sprints SET status = 'failed', completed_at = ?, notes = ? WHERE number = ?",
                (now, reason, args.number),
            )
            if cursor.rowcount == 0:
                print(f"✗ Sprint {args.number} not found.")
                sys.exit(1)
            conn.commit()
            print(f"✓ Sprint {args.number} marked as failed")

        elif args.sprint_action == "note":
            cursor.execute("SELECT notes FROM sprints WHERE number = ?", (args.number,))
            row = cursor.fetchone()
            if not row:
                print(f"✗ Sprint {args.number} not found.")
                sys.exit(1)
            existing = row[0] or ""
            date_tag = f"[{datetime.date.today().isoformat()}]"
            if existing:
                new_notes = existing + "\n\n" + date_tag + " " + (args.notes or "")
            else:
                new_notes = date_tag + " " + (args.notes or "")
            cursor.execute(
                "UPDATE sprints SET notes = ? WHERE number = ?",
                (new_notes, args.number),
            )
            conn.commit()
            print(f"✓ Sprint {args.number} note appended")

    except sqlite3.IntegrityError as e:
        print(f"✗ Database error: {e}")
        if "UNIQUE" in str(e):
            print(f"  Sprint {args.number} already exists.")
        sys.exit(1)
    finally:
        conn.close()


# ─── Command: init ───────────────────────────────────────────────────────────

def cmd_init(args):
    """Bootstrap a new project directory with database, schema, seeds, and registry."""
    db_path = os.path.abspath(args.db_path)
    project_root = os.path.dirname(db_path)
    project_name = args.name or os.path.basename(project_root) or "project"

    # 1. Create directory structure
    os.makedirs(project_root, exist_ok=True)
    for subdir in ["backlog", "sprint", ".opencode/agents"]:
        os.makedirs(os.path.join(project_root, subdir), exist_ok=True)

    # 2. Detect existing sprint work (adoption prompt)
    sprint_01_dir = os.path.join(project_root, "sprint", "01")
    has_sprint_01 = (
        os.path.isfile(os.path.join(sprint_01_dir, "features.md"))
        and os.path.isfile(os.path.join(sprint_01_dir, "brief.md"))
    )
    args.adopt = False

    if has_sprint_01 and not args.yes:
        print("This directory has existing sprint work.")
        answer = input("Seed Sprint 01 as 'manual'? [Y/n] ").strip().lower()
        if answer in ("", "y", "yes"):
            args.adopt = True
        else:
            args.adopt = False
    elif has_sprint_01 and args.yes:
        args.adopt = True
    else:
        args.adopt = False

    # 3. Create or open database and run schema
    conn = sqlite3.connect(db_path)
    try:
        import seed
        exit_code = seed.seed_database(
            db_path=db_path,
            schema_path=args.schema or "schema.sql",
            seed_root=args.seed_root or os.getcwd(),
        )
        if exit_code != 0:
            print("  Schema or seed failed — see messages above.")
            sys.exit(exit_code)
    finally:
        conn.close()

    # 4. Generate agent files from seeded profiles
    agent_dir = os.path.join(project_root, ".opencode", "agents")
    agent_profiles = []
    conn2 = sqlite3.connect(db_path)
    try:
        cursor = conn2.cursor()
        cursor.execute("SELECT name FROM profiles ORDER BY name")
        agent_profiles = [row[0] for row in cursor.fetchall()]
    finally:
        conn2.close()

    for profile_name in agent_profiles:
        print(f"  Generating agent: {profile_name}")
        # Reuse generate logic by calling sm.py's generate directly
        # (We can't call cmd_generate_agent because it needs parsed args)
        # Instead, inline a minimal generate
        conn3 = sqlite3.connect(db_path)
        try:
            cursor = conn3.cursor()
            cursor.execute(
                "SELECT name, version, header, permissions FROM profiles WHERE name = ?",
                (profile_name,),
            )
            row = cursor.fetchone()
            if not row:
                continue
            pname, pver, hdr_json, perm_json = row
            hdr = json.loads(hdr_json)
            perms = json.loads(perm_json)
            cursor.execute(
                """SELECT c.content FROM profile_components pc
                   JOIN components c ON pc.component_id = c.id
                   JOIN profiles p ON pc.profile_id = p.id
                   WHERE p.name = ? ORDER BY pc.order_idx""",
                (profile_name,),
            )
            body_parts = [r[0] for r in cursor.fetchall() if r[0]]
            body = "\n\n".join(body_parts)
            description = hdr.get("role", profile_name)
            mode = hdr.get("mode", "all")
            temperature = hdr.get("temperature", 0.1)
            perm_yaml = _permissions_to_yaml(perms, indent=0)

            agent_md = f"""---
description: {description}
mode: {mode}
temperature: {temperature}
permission:
{perm_yaml}
---

{body}
"""
            output_path = os.path.join(agent_dir, f"{profile_name}.md")
            with open(output_path, "w") as f:
                f.write(agent_md)
            print(f"    → {output_path}")
        finally:
            conn3.close()

    # 5. Write .sm-config.json
    sm_config_path = os.path.join(project_root, SM_CONFIG_FILE)
    with open(sm_config_path, "w") as f:
        json.dump({"db_path": db_path}, f, indent=2)
        f.write("\n")
    print(f"  Config: {sm_config_path}")

    # 6. Adopt Sprint 01 as manual entry if detected
    if args.adopt:
        conn4 = sqlite3.connect(db_path)
        try:
            cursor = conn4.cursor()
            now = datetime.datetime.utcnow().strftime('%Y-%m-%dT%H:%M:%SZ')
            notes = "Sprint 01 built by hand. 7 features, 54 tests, variant test passed."
            cursor.execute(
                """INSERT OR IGNORE INTO sprints (number, mode, status, started_at, completed_at, notes)
                   VALUES (1, 'manual', 'completed', ?, ?, ?)""",
                (now, now, notes),
            )
            conn4.commit()
            if cursor.rowcount > 0:
                print(f"  Sprint 01 adopted as manual entry")
            else:
                print(f"  Sprint 01 already recorded")
        finally:
            conn4.close()

    # 7. Add to project registry
    registry = read_registry()
    registry_upsert(registry, project_name, db_path)
    if not registry.get("default"):
        registry["default"] = project_name
    write_registry(registry)
    print(f"  Registry: {project_name} → {db_path}")

    print()
    print("✓ Project initialised.")
    print(f"  Database: {db_path}")
    print(f"  Agents:   {agent_dir}")


# ─── Command: list projects ──────────────────────────────────────────────────

def cmd_list_projects(args):
    """Display known projects from the registry."""
    registry = read_registry()
    projects = registry.get("projects", [])
    default_name = registry.get("default")

    if not projects:
        print("No projects found. Run 'sm init --db <path>' to create one.")
        return

    if args.json:
        print(json.dumps(registry, indent=2))
        return

    headers = ("Name", "DB Path", "Created", "Last Opened")
    col_widths = [24, 50, 14, 14]
    fmt = "  ".join("{{:<{}}}".format(w) for w in col_widths)
    print(fmt.format(*headers))
    print("  ".join("─" * w for w in col_widths))
    for proj in projects:
        name = proj["name"]
        if name == default_name:
            name += " (default)"
        print(fmt.format(
            name,
            proj.get("db_path", ""),
            proj.get("created", "")[:10],
            proj.get("last_opened", "")[:10],
        ))


# ─── Command: projects ───────────────────────────────────────────────────────

def cmd_projects(args):
    """Manage project registry entries."""
    registry = read_registry()

    if args.projects_action == "default":
        # Find the project by name
        found = any(p["name"] == args.name for p in registry.get("projects", []))
        if not found:
            print(f"✗ Project '{args.name}' not found in registry.")
            sys.exit(1)
        registry["default"] = args.name
        write_registry(registry)
        print(f"✓ Default project set to '{args.name}'")

    elif args.projects_action == "remove":
        original_len = len(registry.get("projects", []))
        registry["projects"] = [
            p for p in registry.get("projects", []) if p["name"] != args.name
        ]
        if len(registry["projects"]) == original_len:
            print(f"✗ Project '{args.name}' not found in registry.")
            sys.exit(1)
        # Clear default if it was the removed project
        if registry.get("default") == args.name:
            registry["default"] = None
        write_registry(registry)
        print(f"✓ Project '{args.name}' removed from registry")


# ─── YAML helper ─────────────────────────────────────────────────────────────

def _permissions_to_yaml(perms, indent=0):
    """Convert a permissions dict to YAML-like string without PyYAML.

    Produces properly indented YAML for the permission block.
    Keys containing special YAML characters (like '*') are quoted.
    """
    lines = []
    prefix = "  " * (indent + 1)

    def needs_quoting(s):
        """Check if a YAML key needs quoting (contains special chars)."""
        special = {"*", "?", "&", "!", "|", ">", "[", "]", "{", "}", "%"}
        return any(c in special for c in s) or ":" in s or "#" in s

    if isinstance(perms, dict):
        for key, value in perms.items():
            yaml_key = json.dumps(key) if needs_quoting(key) else key
            if isinstance(value, dict):
                lines.append(f"{prefix}{yaml_key}:")
                lines.append(_permissions_to_yaml(value, indent=indent + 1))
            elif isinstance(value, str):
                lines.append(f"{prefix}{yaml_key}: {value}")
            else:
                lines.append(f"{prefix}{yaml_key}: {json.dumps(value)}")
    elif isinstance(perms, str):
        lines.append(f"{prefix}{perms}")

    return "\n".join(lines)


# ─── Argument parser ────────────────────────────────────────────────────────

def build_parser():
    """Build the argument parser with subcommands."""
    parser = argparse.ArgumentParser(
        prog="sm",
        description="Matsya: State machine CLI",
    )
    parser.add_argument("--db", default=None, help="SQLite database path (resolved via .sm-config.json, registry, or fallback)")
    subparsers = parser.add_subparsers(dest="command", help="Available commands")

    # ── seed ──
    p_seed = subparsers.add_parser("seed", help="Populate database from seed files")
    p_seed.add_argument("--schema", default="schema.sql", help="Schema SQL file path")
    p_seed.add_argument("--seed-root", default=".", help="Root directory containing seed data")
    p_seed.set_defaults(func=cmd_seed)

    # ── run ──
    p_run = subparsers.add_parser("run", help="Load a profile and start the state machine loop (auto-creates sprint)")
    p_run.add_argument("--profile", required=True, help="Profile name to load")
    p_run.add_argument("--config", default=None, help="Config JSON file path")
    p_run.add_argument("--max-iterations", type=int, default=None, help="Override max iterations")
    p_run.add_argument("--max-retries", type=int, default=None, help="Override max retries")
    p_run.set_defaults(func=cmd_run)

    # ── init ──
    p_init = subparsers.add_parser("init", help="Bootstrap a new project directory")
    p_init.add_argument("db_path", metavar="DB_PATH", help="Database path (e.g. matsya.db)")
    p_init.add_argument("--name", default=None, help="Project name (default: directory basename)")
    p_init.add_argument("--schema", default="schema.sql", help="Schema SQL file path")
    p_init.add_argument("--seed-root", default=None, help="Root directory containing seed data")
    p_init.add_argument("--yes", "-y", action="store_true", help="Auto-accept adoption prompts")
    p_init.set_defaults(func=cmd_init)

    # ── list ──
    p_list = subparsers.add_parser("list", help="List items from the database")
    p_list_sub = p_list.add_subparsers(dest="list_target", help="What to list")

    p_list_profiles = p_list_sub.add_parser("profiles", help="Display all profiles")
    p_list_profiles.add_argument("--verbose", "-v", action="store_true", help="Show permissions")
    p_list_profiles.add_argument("--json", action="store_true", help="Output as JSON")
    p_list_profiles.set_defaults(func=cmd_list_profiles)

    p_list_components = p_list_sub.add_parser("components", help="Display all components")
    p_list_components.add_argument("--verbose", "-v", action="store_true", help="Show full content")
    p_list_components.add_argument("--json", action="store_true", help="Output as JSON")
    p_list_components.add_argument("--truncate", type=int, default=60, help="Content preview length")
    p_list_components.set_defaults(func=cmd_list_components)

    p_list_projects = p_list_sub.add_parser("projects", help="Display known projects from registry")
    p_list_projects.add_argument("--json", action="store_true", help="Output as JSON")
    p_list_projects.set_defaults(func=cmd_list_projects)

    # ── log ──
    p_log = subparsers.add_parser("log", help="Display execution history (sprints + phase runs)")
    p_log.add_argument("--sprint", type=int, default=None, help="Filter by sprint number")
    p_log.add_argument("--phases", dest="show_phases", action="store_true", help="Show phase run detail")
    p_log.add_argument("--json", action="store_true", help="Output as JSON")
    p_log.set_defaults(func=cmd_log)

    # ── sprint ──
    p_sprint = subparsers.add_parser("sprint", help="Manage sprint lifecycle (start, complete, fail, note)")
    p_sprint_sub = p_sprint.add_subparsers(dest="sprint_action", help="Sprint action")

    p_sprint_start = p_sprint_sub.add_parser("start", help="Start a new sprint")
    p_sprint_start.add_argument("--number", "-n", type=int, required=True, help="Sprint number")
    p_sprint_start.add_argument("--mode", choices=["driven", "manual", "hybrid"], default="driven", help="Sprint mode")
    p_sprint_start.add_argument("--notes", default=None, help="Initial notes")
    p_sprint_start.set_defaults(func=cmd_sprint)

    p_sprint_complete = p_sprint_sub.add_parser("complete", help="Mark a sprint as completed")
    p_sprint_complete.add_argument("--number", "-n", type=int, required=True, help="Sprint number")
    p_sprint_complete.set_defaults(func=cmd_sprint)

    p_sprint_fail = p_sprint_sub.add_parser("fail", help="Mark a sprint as failed")
    p_sprint_fail.add_argument("--number", "-n", type=int, required=True, help="Sprint number")
    p_sprint_fail.add_argument("--reason", default=None, help="Reason for failure")
    p_sprint_fail.set_defaults(func=cmd_sprint)

    p_sprint_note = p_sprint_sub.add_parser("note", help="Append a note to a sprint")
    p_sprint_note.add_argument("--number", "-n", type=int, required=True, help="Sprint number")
    p_sprint_note.add_argument("--notes", required=True, help="Note text to append")
    p_sprint_note.set_defaults(func=cmd_sprint)

    # ── projects ──
    p_projects = subparsers.add_parser("projects", help="Manage project registry entries")
    p_projects_sub = p_projects.add_subparsers(dest="projects_action", help="Projects action")

    p_projects_default = p_projects_sub.add_parser("default", help="Set the default project")
    p_projects_default.add_argument("name", help="Project name from registry")
    p_projects_default.set_defaults(func=cmd_projects)

    p_projects_remove = p_projects_sub.add_parser("remove", help="Remove a project from registry")
    p_projects_remove.add_argument("name", help="Project name to remove")
    p_projects_remove.set_defaults(func=cmd_projects)

    # ── status ──
    p_status = subparsers.add_parser("status", help="Show current system state")
    p_status.add_argument("--backlog", default=None, help="Backlog directory or file path")
    p_status.add_argument("--signal", default=None, help="Signal file path")
    p_status.add_argument("--state", default=None, help="State file path")
    p_status.set_defaults(func=cmd_status)

    # ── generate ──
    p_gen = subparsers.add_parser("generate", help="Generate artifacts from profiles")
    p_gen_sub = p_gen.add_subparsers(dest="generate_target", help="What to generate")

    p_gen_agent = p_gen_sub.add_parser("agent", help="Generate an OpenCode agent file")
    p_gen_agent.add_argument("name", help="Profile name to render")
    p_gen_agent.add_argument("--output-dir", default=None, help="Output directory (default: .opencode/agents)")
    p_gen_agent.set_defaults(func=cmd_generate_agent)

    return parser


# ─── Entry point ────────────────────────────────────────────────────────────

def main():
    parser = build_parser()
    args = parser.parse_args()

    if args.command is None:
        parser.print_help()
        sys.exit(1)

    # Handle sub-subcommands
    if args.command == "list" and args.list_target is None:
        parser.parse_args(["list", "--help"])
        sys.exit(1)

    if args.command == "generate" and args.generate_target is None:
        parser.parse_args(["generate", "--help"])
        sys.exit(1)

    if args.command == "sprint" and args.sprint_action is None:
        parser.parse_args(["sprint", "--help"])
        sys.exit(1)

    if args.command == "projects" and args.projects_action is None:
        parser.parse_args(["projects", "--help"])
        sys.exit(1)

    args.func(args)


if __name__ == "__main__":
    main()
